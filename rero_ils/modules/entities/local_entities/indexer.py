# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity indexer APIs."""

from datetime import UTC, datetime

from celery import shared_task
from flask import current_app

from rero_ils.modules.api import IlsRecordsIndexer, ReferencedRecordsIndexer
from rero_ils.modules.utils import (
    get_indexer_class_by_resource,
    get_record_class_by_resource,
)

from ..dumpers import indexer_dumper
from .api import LocalEntity


@shared_task(ignore_result=True)
def index_referenced_records(entity):
    """Index referenced records."""
    indexer = ReferencedRecordsIndexer()
    entity = LocalEntity.get_record_by_pid(entity.get("pid"))
    if referenced_resources := entity.get_links_to_me(get_pids=True):
        for resource, pids in referenced_resources.items():
            record_cls = get_record_class_by_resource(resource)
            indexer_cls = get_indexer_class_by_resource(resource)
            pid_type = record_cls.provider.pid_type
            referenced = []
            for pid in pids:
                record = record_cls.get_record_by_pid(pid)
                referenced.append({"pid_type": pid_type, "record": record})
            indexer.index(indexer_cls, referenced)


class LocalEntitiesIndexer(IlsRecordsIndexer):
    """Local entity indexing class."""

    record_cls = LocalEntity
    # data dumper for indexing
    record_dumper = indexer_dumper

    def index(self, entity, arguments=None, **kwargs):
        """Index a Local entity record."""
        super().index(entity)
        eta = datetime.now(UTC) + current_app.config.get("RERO_ILS_INDEXER_TASK_DELAY", 0)
        index_referenced_records.apply_async((entity,), eta=eta)

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type="locent")
