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

"""Files Operations."""

from flask import current_app
from invenio_records_resources.services.uow import Operation

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
        raise NotImplementedError


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
