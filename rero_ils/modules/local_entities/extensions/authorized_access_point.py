# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Document record extension to add the MEF pid in the database."""


from invenio_records.extensions import RecordExtension


class AuthorizedAccessPointExtension(RecordExtension):
    """Adds the authorized access point."""

    def _generate_authorized_access_point(self, record):
        """Generate authorized access point.

        :params record: dict - a document record.
        """
        record['authorized_access_point'] = record.get('preferred_name')

    def pre_create(self, record):
        """Called after a record is initialized.

        :param record: dict - the record to be modified.
        """
        self._generate_authorized_access_point(record)
        # required for validation
        if record.model:
            record.model.data = record

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: dict - the record to be modified.
        """
        self._generate_authorized_access_point(record)
