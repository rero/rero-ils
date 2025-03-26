# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Celery tasks for documents."""

from datetime import datetime, timedelta

import click
from celery import shared_task
from flask import current_app
from invenio_search import current_search_client

from rero_ils.modules.utils import set_timestamp


@shared_task(ignore_result=True)
def reindex_document(pid):
    """Reindex a document.

    :param pid: str - pid value of the document to reindex.
    """
    from rero_ils.modules.documents.api import Document

    Document.get_record_by_pid(pid).reindex()


@shared_task(ignore_result=True)
def delete_orphan_harvested(delete=False, verbose=False):
    """Delete orphan harvested documents.

    :param delete: if True delete from DB and ES.
    :param verbose: Verbose print.
    :returns: count of deleted documents.
    """
    from rero_ils.modules.documents.api import Document, DocumentsSearch

    query = (
        DocumentsSearch()
        .filter("term", harvested=True)
        .exclude("exists", field="holdings")
    )
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

    :param days: Delete drafts older then days.
    :param delete: if True delete from DB and ES.
    :param verbose: Verbose print.
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
    """Reindex the items of document.

    :param pid: str - pid value of the document to reindex.
    """
    from rero_ils.modules.items.api import ItemsSearch

    for hit in (
        ItemsSearch().extra(version=True).filter("term", document__pid=record["pid"])
    ):
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
