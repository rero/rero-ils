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

from invenio_records_resources.services.uow import Operation

from rero_ils.modules.documents.tasks import reindex_document


class ReindexDoc(Operation):
    """Reindex a given document."""

    def __init__(self, pid):
        """Constructor.

        :param pid: str - document pid value.
        """
        self.pid = pid

    def __eq__(self, other):
        """Comparison method.

        :param other: obj - instance to compare with.
        """
        return isinstance(other, ReindexDoc) and self.pid == other.pid

    def on_post_commit(self, uow):
        """Run the post task operation.

        :param uow: obj - UnitOfWork instance.
        """
        reindex_document.delay(self.pid)
