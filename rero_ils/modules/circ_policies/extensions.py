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

"""Circulation policy record extensions."""

from invenio_records.extensions import RecordExtension


class CircPolicyFieldsExtension(RecordExtension):
    """Extension to manage circulation policy fields."""

    def _pickup_hold_duration_check(self, record):
        """Manage the pickup hold duration field.

        If the circulation policy doesn't allow request, no need to keep the
        `pickup_hold_duration` field.

        :param record: the record to check.
        """
        if not record.get('allow_requests') \
           and 'pickup_hold_duration' in record:
            del record['pickup_hold_duration']

    pre_commit = _pickup_hold_duration_check
    pre_create = _pickup_hold_duration_check
