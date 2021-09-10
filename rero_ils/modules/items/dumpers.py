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

"""Items dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class ItemNotificationDumper(InvenioRecordsDumper):
    """Item dumper class for notification."""

    def dump(self, record, data):
        """Dump an item instance for notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        location = record.get_location()
        data = {
            'pid': record.pid,
            'barcode': record.get('barcode'),
            'call_numbers': record.call_numbers,
            'location_name': location.get('name'),
            'library_name': location.get_library().get('name')
        }
        data = {k: v for k, v in data.items() if v}
        return data
