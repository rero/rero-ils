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

"""Holdings dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class ClaimIssueHoldingDumper(InvenioRecordsDumper):
    """Dumper class use by claim issue notification for holding information."""

    def dump(self, record, data):
        """Dump a holdings instance with necessary information.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :returns: original data with addition holding information.
        :rtype: dict
        """
        assert record.is_serial, "Holding type must be 'serial'"
        data = {
            'pid': record.pid,
            'client_id': record.get('client_id'),
            'order_reference': record.get('order_reference')
        }
        return {k: v for k, v in data.items() if v}
