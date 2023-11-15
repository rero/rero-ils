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

"""Operation logs API."""

import hashlib

from rero_ils.modules.locations.api import Location
from rero_ils.modules.utils import extracted_data_from_ref


class SpecificOperationLog():
    """Specific Operation log."""

    @classmethod
    def _get_patron_data(cls, patron):
        """Get patron record data.

        :param str patron: Patron record
        :returns: Patron formatted data
        """
        patron_type = None

        if patron.get('patron'):
            patron_type = extracted_data_from_ref(
                patron['patron']['type'], data='record')

        hashed_pid = hashlib.md5(patron.pid.encode()).hexdigest()
        data = {
            'name': patron.formatted_name,
            'type': patron_type['name'] if patron_type else None,
            'age': patron.age,
            'postal_code': patron.user.user_profile.get(
                'postal_code', 'no_information'),
            'gender': patron.user.user_profile.get('gender', 'no_information'),
            'pid': patron.pid,
            'hashed_pid': hashed_pid
        }

        if patron.get('local_codes'):
            data['local_codes'] = patron['local_codes']

        return data

    @classmethod
    def _get_item_data(cls, item):
        """Get item record data.

        :param str item: Item record
        :returns: Item formatted data
        """
        data = {
            'pid': item.pid,
            'library_pid': item.library_pid,
            'category': item['type'],
            'document': cls._get_document_data(
                extracted_data_from_ref(item['document'], data='record')),
            'holding': cls._get_holding_data(
                extracted_data_from_ref(item['holding'], data='record'))
        }
        if item.get('call_number'):
            data['call_number'] = item.get('call_number')
        if item.get('enumerationAndChronology'):
            data['enumerationAndChronology'] =\
                item.get('enumerationAndChronology')
        return data

    @classmethod
    def _get_document_data(cls, document):
        """Get document record data.

        :param str document: Document record
        :returns: Document formatted data
        """
        document = document.dumps()
        return {
            'pid': document['pid'],
            'title': next(filter(lambda x: x.get('type') == 'bf:Title',
                                 document.get('title'))
                          ).get('_text'),
            'type':
            document['type'][0].get('subtype',
                                    document['type'][0]['main_type'])
        }

    @classmethod
    def _get_holding_data(cls, holding):
        """Get holding record data.

        :param str holding: Holding record
        :returns: Holding formatted data
        """
        return {
            'pid': holding.pid,
            'location_name': cls._get_location_name(holding.location_pid)
        }

    @classmethod
    def _get_location_name(cls, location_pid):
        """Get location name for a location PID.

        :param str location_pid: Location PID
        :returns: Location name
        """
        location = Location.get_record_by_pid(location_pid)
        return location['name']
