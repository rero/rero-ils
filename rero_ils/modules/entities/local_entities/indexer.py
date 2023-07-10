# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Local entity indexer APIs."""
from datetime import datetime

from celery import shared_task
from flask import current_app

from rero_ils.modules.api import IlsRecordsIndexer, ReferencedRecordsIndexer
from rero_ils.modules.utils import get_indexer_class_by_resource, \
    get_record_class_by_resource

from .api import LocalEntity
from ..dumpers import indexer_dumper


@shared_task(ignore_result=True)
def index_referenced_records(entity):
    """Index referenced records."""
    indexer = ReferencedRecordsIndexer()
    entity = LocalEntity.get_record_by_pid(entity.get('pid'))
    if referenced_resources := entity.get_links_to_me(get_pids=True):
        for resource, pids in referenced_resources.items():
            record_cls = get_record_class_by_resource(resource)
            indexer_cls = get_indexer_class_by_resource(resource)
            pid_type = record_cls.provider.pid_type
            referenced = []
            for pid in pids:
                record = record_cls.get_record_by_pid(pid)
                referenced.append(dict(
                        pid_type=pid_type,
                        record=record
                ))
            indexer.index(indexer_cls, referenced)


class LocalEntitiesIndexer(IlsRecordsIndexer):
    """Local entity indexing class."""

    record_cls = LocalEntity
    # data dumper for indexing
    record_dumper = indexer_dumper

    def index(self, entity, arguments=None, **kwargs):
        """Index a Local entity record."""
        super().index(entity)
        eta = datetime.utcnow() + current_app.config.get(
            "RERO_ILS_INDEXER_TASK_DELAY", 0)
        index_referenced_records.apply_async((entity,), eta=eta)

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='locent')
