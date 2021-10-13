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

"""Libraries dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class LibraryCirculationNotificationDumper(InvenioRecordsDumper):
    """Library dumper class for circulation notification."""

    def dump(self, record, data):
        """Dump a library instance for circulation notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        data.update({
            'pid': record.pid,
            'name': record.get('name'),
            'address': record.get('address'),
            'email': record.get('email')
        })
        return {k: v for k, v in data.items() if v}
