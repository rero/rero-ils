# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Celery tasks for `Entity` records."""

import click
from celery import shared_task
from flask import current_app

from .api import RemoteEntity
from .replace import ReplaceIdentifiedBy
from .sync import SyncEntity


@shared_task(ignore_result=True)
def delete_records(records, verbose=False):
    """Records deletion and indexing.

    :param records: records to delete
    :param verbose: verbose output
    :return: count of records
    """
    for record in records:
        status = RemoteEntity.delete(record, force=False, dbcommit=True, delindex=True)
        current_app.logger.info(f"record: {record.id} | DELETED {status}")
        # TODO bulk update and reindexing
    if verbose:
        click.echo(f"records deleted: {len(records)}")
    return len(records)


@shared_task(ignore_result=True)
def sync_entities(from_last_date=True, verbose=0, dry_run=False, in_memory=True):
    """Synchronize the entities within the MEF server.

    :param from_last_date: (boolean) if True try to consider agent modified
        after the last run date time
    :param verbose: (boolean|integer) verbose level
    :param dry_run: (boolean) if true the data are not modified
    """
    sync_entity = SyncEntity(from_last_date=from_last_date, verbose=verbose, dry_run=dry_run)
    n_doc_updated, n_mef_updated, sync_mef_errors = sync_entity.sync(in_memory=in_memory)
    n_mef_removed, clean_mef_errors = sync_entity.remove_unused()
    return {
        "n_doc_updated": n_doc_updated,
        "n_mef_updated": n_mef_updated,
        "clean_mef_errors": clean_mef_errors,
        "sync_mef_errors": sync_mef_errors,
        "n_mef_removed": n_mef_removed,
    }


@shared_task(ignore_result=True)
def replace_identified_by(fields=None, verbose=0, dry_run=False):
    """Replace identifiedBy with $ref.

    :param fields: Entity type to replace (concepts, subjects, genreForm)
    :param verbose: (boolean|integer) verbose level
    :param dry_run: (boolean) if true the data are not modified
    """
    fields = fields or ["contribution", "subjects", "genreForm"]
    result = {}
    for field in fields:
        try:
            replace = ReplaceIdentifiedBy(field=field, verbose=verbose, dry_run=dry_run)
            changed, not_found, rero_only = replace.run()
            replace.set_timestamp()
            result[field] = {
                "changed": changed,
                "not_found": not_found,
                "rero_only": rero_only,
            }
        except Exception as err:
            result[field] = {"error": err}
    return result
