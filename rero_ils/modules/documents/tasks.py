# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Celery tasks for documents."""

import time
from datetime import datetime, timedelta

import click
import redis as redis_module
from celery import shared_task
from flask import current_app
from invenio_db import db
from invenio_search import current_search_client

from rero_ils.modules.utils import set_timestamp


@shared_task(ignore_result=True)
def reindex_document(pid):
    """Reindex a document.

    :param pid: str - PID value of the document to reindex.
    """
    from rero_ils.modules.documents.api import Document

    Document.get_record_by_pid(pid).reindex()


@shared_task(ignore_result=True)
def delete_orphan_harvested(delete=False, verbose=False):
    """Delete orphan harvested documents.

    :param delete: if True, delete from DB and search.
    :param verbose: if True, print progress output to the terminal.
    :returns: count of deleted documents.
    """
    from rero_ils.modules.documents.api import Document, DocumentsSearch

    query = DocumentsSearch().filter("term", harvested=True).exclude("exists", field="holdings")
    pids = [hit.pid for hit in query.source("pid").scan()]
    count = 0

    if verbose:
        click.secho(f"Orphan harvested documents count: {len(pids)}", fg="yellow")
    for pid in pids:
        if doc := Document.get_record_by_pid(pid):
            if verbose:
                click.secho(f"Deleting orphan harvested: {pid}", fg="yellow")
            if delete:
                try:
                    # only delete documents that have no links to me, only reason not to delete should be 'harvested'
                    if doc.reasons_not_to_delete() == {"others": {"harvested": True}}:
                        doc.pop("harvested")
                        doc.replace(doc, dbcommit=True, reindex=True)
                        doc.delete(dbcommit=True, delindex=True)
                        count += 1
                except Exception:
                    msg = f"COULD NOT DELETE ORPHAN HARVESTED: {pid} {doc.reasons_not_to_delete()}"
                    if verbose:
                        click.secho(f"ERROR: {msg}", fg="red")
                    current_app.logger.warning(msg)

    set_timestamp("delete_orphan_harvested", deleted=count)
    return count


@shared_task(ignore_result=True)
def delete_drafts(days=1, delete=False, verbose=False):
    """Delete drafts.

    :param days: delete drafts older than this number of days.
    :param delete: if True, delete from DB and search.
    :param verbose: if True, print progress output to the terminal.
    :returns: count of deleted drafts.
    """
    from rero_ils.modules.documents.api import Document, DocumentsSearch

    days_ago = datetime.now() - timedelta(days=days)
    query = (
        DocumentsSearch()
        .filter("exists", field="_draft")
        .filter("range", _created={"lte": days_ago})
        .params(preserve_order=True)
        .sort({"_created": {"order": "asc"}})
    )
    pids = [hit.pid for hit in query.source("pid").scan()]
    count = len(pids)
    if verbose:
        click.secho(f"Delete drafts {days_ago} count: {count}", fg="yellow")
    for pid in pids:
        if doc := Document.get_record_by_pid(pid):
            if verbose:
                click.secho(f"Delete draft: {pid} {doc.created}", fg="yellow")
            if delete:
                try:
                    doc.delete(dbcommit=True, delindex=True)
                except Exception:
                    count -= 1
                    msg = f"COULD NOT DELETE DRAFT: {pid} {doc.reasons_not_to_delete()}"
                    if verbose:
                        click.secho(f"ERROR: {msg}", fg="red")
                    current_app.logger.warning(msg)

    set_timestamp("delete_drafts", deleted=count)
    return count


@shared_task(ignore_result=True)
def reindex_document_items(record):
    """Reindex the items of a document and update their document_type if it changed.

    :param record: dict - the document record containing at least ``pid`` and ``type``.
    """
    from rero_ils.modules.items.api import ItemsSearch

    query = ItemsSearch().extra(version=True).filter("term", document__pid=record["pid"])
    items_count = query.count()
    for hit in query.scan():
        data = hit.to_dict()
        # update the document type in item if different.
        if data["document"]["document_type"] != record["type"]:
            data["document"]["document_type"] = record["type"]
            current_search_client.index(
                index=ItemsSearch.Meta.index,
                id=hit.meta.id,
                body=data,
                version=hit.meta.version,
                version_type="external_gte",
            )
    return items_count


def _cover_url_redis():
    """Return a Redis client for the cover URL queue."""
    return redis_module.StrictRedis.from_url(current_app.config["CACHE_REDIS_URL"])


def enqueue_cover_url_update(pid, cached=True):
    """Add a document PID to the cover URL queue and start the worker if idle.

    Uses a Redis set so that multiple rapid saves of the same document result
    in a single queue entry. The worker is started only when the lock key is
    absent and the queue is not paused, ensuring at most one worker runs at a
    time.

    When the queue is paused (``cover-url-queue-worker pause``), PIDs still
    accumulate so that ``cover-url-queue-worker resume`` can process them all
    at once.

    :param pid: str - PID of the document needing a cover URL.
    :param cached: bool - passed through to the thumbnail lookup.
    """
    r = _cover_url_redis()
    queue_key = current_app.config.get("RERO_ILS_COVER_URL_QUEUE_KEY", "rero_ils:cover_url_queue")
    worker_key = current_app.config.get("RERO_ILS_COVER_URL_WORKER_KEY", "rero_ils:cover_url_worker")
    paused_key = current_app.config.get("RERO_ILS_COVER_URL_PAUSED_KEY", "rero_ils:cover_url_paused")
    delay = current_app.config.get("RERO_ILS_COVER_URL_TASK_DELAY", 10)
    r.sadd(queue_key, pid)
    # NX: only set if the key does not exist — i.e. no worker is running yet.
    if not r.exists(paused_key) and r.set(worker_key, 1, nx=True, ex=3600):
        process_cover_url_queue.apply_async(kwargs={"cached": cached}, countdown=delay)


@shared_task(ignore_result=True)
def process_cover_url_queue(cached=True):
    """Pop one PID from the cover URL queue and add its cover image.

    After processing one document the task reschedules itself with a delay,
    serialising all lookups and avoiding concurrent writes to the same row.
    When the queue is empty the worker lock is released so the next call to
    ``enqueue_cover_url_update`` can start a fresh worker.

    :param cached: bool - if True, use cached thumbnails from the provider.
    """
    from rero_ils.modules.documents.api import Document
    from rero_ils.modules.documents.extensions.add_cover_url import AddCoverUrlExtension

    r = _cover_url_redis()
    queue_key = current_app.config.get("RERO_ILS_COVER_URL_QUEUE_KEY", "rero_ils:cover_url_queue")
    worker_key = current_app.config.get("RERO_ILS_COVER_URL_WORKER_KEY", "rero_ils:cover_url_worker")
    delay = current_app.config.get("RERO_ILS_COVER_URL_TASK_DELAY", 10)

    raw = r.spop(queue_key)
    if raw:
        pid = raw.decode() if isinstance(raw, bytes) else raw
        document = Document.get_record_by_pid(pid)
        if document and AddCoverUrlExtension(cached=cached).add_cover_url(document):
            current_app.logger.debug(f"Adding cover URL for {pid} from queue: {document.cover}")
            try:
                # pre_commit / post_commit are no-ops: cover already in record.
                document.update(data=document, commit=True, dbcommit=True, reindex=True)
            except Exception:
                current_app.logger.exception(f"Failed to update cover URL for document {pid}")
        process_cover_url_queue.apply_async(kwargs={"cached": cached}, countdown=delay)
    else:
        # Queue drained — release lock, then guard against a concurrent enqueue.
        r.delete(worker_key)
        if r.scard(queue_key) > 0 and r.set(worker_key, 1, nx=True, ex=3600):
            process_cover_url_queue.apply_async(kwargs={"cached": cached}, countdown=delay)


@shared_task(ignore_result=True)
def add_cover_urls(commit=False, verbose=False, cached=True, delay=0):
    """Add cover URLs to all documents with ISBNs.

    :param commit: if True, commit changes to the database.
    :param verbose: if True, print progress output to the terminal.
    :param cached: if True, use cached thumbnails from the provider.
    :param delay: seconds to sleep between requests to avoid stressing external servers.
    :returns: dict - count of updated documents per provider.
    """
    from rero_ils.modules.documents.api import Document, DocumentsSearch
    from rero_ils.modules.documents.extensions.add_cover_url import AddCoverUrlExtension

    # Get pids from search query
    search = (
        DocumentsSearch()
        .filter("term", identifiedBy__type="bf:Isbn")
        .exclude("term", electronicLocator__content="coverImage")
        .params(preserve_order=True)
        .source("pid")
    )
    pids = [hit.pid for hit in search.scan()]
    # Sort numeric pids numerically, non-numeric pids alphabetically after the numeric ones
    pids = sorted(pids, key=lambda x: (0, int(x)) if x.isdigit() else (1, x))

    provider_counts = {}
    extension = AddCoverUrlExtension(cached=cached)

    db.session.close()  # close DB session to avoid timeout during long processing
    # Process all pids
    for idx, pid in enumerate(pids, 1):
        if document := Document.get_record_by_pid(pid):
            # Always runs sync regardless of async config; mutates record in-place,
            # returns True only if a locator was newly added.
            if extension.add_cover_url(document):
                url, provider = document.cover
                provider_counts.setdefault(provider, 0)
                provider_counts[provider] += 1
                if verbose:
                    click.echo(f"{idx:<10} document: {document.pid:<10} {provider or '':<15} {url}")
                if commit:
                    try:
                        # pre_commit is a no-op here: _has_cover() is already True
                        document.update(data=document, commit=True, dbcommit=True, reindex=True)
                    except Exception:
                        current_app.logger.exception(f"Failed to update cover URL for document {pid}")
            if delay:
                time.sleep(delay)

    provider_counts["all"] = sum(provider_counts.values())
    if commit:
        set_timestamp("add_cover_urls", updated=provider_counts)
    return provider_counts
