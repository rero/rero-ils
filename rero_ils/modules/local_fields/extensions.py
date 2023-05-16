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

"""`LocalField` record extensions."""
from invenio_records.extensions import RecordExtension


class DeleteRelatedLocalFieldExtension(RecordExtension):
    """Extension managing LocalFields deletion when parent resource is deleted.

    `LocalFields` should not be a reason to block suppression of related
    resource. But if the parent resource is deleted, then the related
    `LocalFields` must be deleted too to avoid LocalField orphan.
    """

    def pre_delete(self, record, force=False):
        """Called before a record is deleted.

        :param record: the parent related record.
        :param force: is the suppression must be forced.
        """
        from .api import LocalField
        for local_field in LocalField.get_local_fields(record):
            local_field.delete(force=force, delindex=True)
