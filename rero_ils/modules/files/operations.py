# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Files Operations."""

from flask import current_app
from invenio_records_resources.services.uow import Operation
from invenio_search import current_search

from rero_ils.modules.documents.tasks import reindex_document


class ReindexOperationBase(Operation):
    """Base class for reindex operations."""

    def __init__(self, id):
        """Constructor.

        :param pid: str - document pid value.
        """
        self.id = id

    def __eq__(self, other):
        """Comparison method.

        :param other: obj - instance to compare with.
        """
        return isinstance(other, self.__class__) and self.id == other.id

    def on_post_commit(self, uow):
        """Run the post task operation.

        :param uow: obj - UnitOfWork instance.
        """
        raise NotImplementedError()


class ReindexDoc(ReindexOperationBase):
    """Reindex a given document."""

    def on_post_commit(self, uow):
        """Run the post task operation.

        :param uow: obj - UnitOfWork instance.
        """
        reindex_document.delay(self.id)


class ReindexRecordFile(ReindexOperationBase):
    """Reindex a given record file."""

    def __init__(self, id):
        """Constructor.

        :param pid: str - record file id value.
        """
        ext = current_app.extensions["rero-invenio-files"]
        # get services
        self.record_service = ext.records_service
        super().__init__(id)

    def on_post_commit(self, uow):
        """Run the post task operation.

        :param uow: obj - UnitOfWork instance.
        """
        self.record_service.indexer.index_by_id(self.id)
        # index flush needed for following ReindexDoc.on_post_commit
        current_search.flush_and_refresh(self.record_service.record_cls.index._name)
