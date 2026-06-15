# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Celery tasks to index records."""

from celery import shared_task

from .api import IlsRecordsIndexer
from .utils import set_timestamp


@shared_task(ignore_result=True)
def process_bulk_queue(version_type=None, queue=None, search_bulk_kwargs=None, stats_only=True):
    """Process bulk indexing queue.

    :param str version_type: search index version type.
    :param str queue: Queue name to use (also used as routing key).
    :param dict search_bulk_kwargs: Passed to
        :func:`elasticsearch:elasticsearch.helpers.bulk`.
    :param boolean stats_only: if `True` only report number of
            successful/failed operations instead of just number of
            successful and a list of error responses.
    Note: You can start multiple versions of this task.
    """
    from .cli.index import connect_queue

    connected_queue = connect_queue(name=queue) if queue else None
    indexer = IlsRecordsIndexer(version_type=version_type, queue=connected_queue, routing_key=queue)
    return indexer.process_bulk_queue(search_bulk_kwargs=search_bulk_kwargs, stats_only=stats_only)


@shared_task(ignore_result=True)
def scheduler_timestamp():
    """Writes a time stamp to current cache."""
    time = set_timestamp("scheduler")
    return {"scheduler": time}
