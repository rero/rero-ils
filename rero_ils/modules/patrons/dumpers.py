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

"""Patron dumpers."""
from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class PatronNotificationDumper(InvenioRecordsDumper):
    """Patron dumper class for notification."""

    def dump(self, record, data, **kwargs):
        """Dump a patron instance for notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        data = {
            'pid': record.pid,
            'last_name': data.get('last_name'),
            'first_name': data.get('first_name'),
            'profile_url': record.profile_url,
            'address': {
                'street': data.get('street'),
                'postal_code': data.get('postal_code'),
                'city': data.get('city'),
                'country': data.get('country')
            },
            'barcode': record.get('patron', {}).get('barcode')
        }
        data['address'] = {k: v for k, v in data['address'].items() if v}
        data = {k: v for k, v in data.items() if v}
        return data
