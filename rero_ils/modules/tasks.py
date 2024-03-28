# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Celery tasks to index records."""

from celery import shared_task
from celery.messaging import establish_connection

from .api import IlsRecordsIndexer
from .utils import set_timestamp


@shared_task(ignore_result=True)
def process_bulk_queue(version_type=None, queue=None, search_bulk_kwargs=None,
                       stats_only=True):
    """Process bulk indexing queue.

    :param str version_type: Elasticsearch version type.
    :param Queue queue: Queue to use.
    :param str routing_key: Routing key to use.
    :param dict search_bulk_kwargs: Passed to
        :func:`elasticsearch:elasticsearch.helpers.bulk`.
    :param boolean stats_only: if `True` only report number of
            successful/failed operations instead of just number of
            successful and a list of error responses.
    Note: You can start multiple versions of this task.
    """
    from .cli.index import connect_queue

    connected_queue = None
    if queue:
        connection = establish_connection()
        connected_queue = connect_queue(connection, queue)
    indexer = IlsRecordsIndexer(
        version_type=version_type,
        queue=connected_queue,
        routing_key=queue
    )
    return indexer.process_bulk_queue(
        search_bulk_kwargs=search_bulk_kwargs, stats_only=stats_only)


@shared_task(ignore_result=True)
def scheduler_timestamp():
    """Writes a time stamp to current cache."""
    time = set_timestamp('scheduler')
    return {'scheduler': time}
