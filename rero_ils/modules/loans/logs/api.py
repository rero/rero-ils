# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Loans logs API."""

from ...documents.api import Document
from ...holdings.api import Holding
from ...items.api import Item
from ...locations.api import Location
from ...operation_logs.api import OperationLog
from ...patron_types.api import PatronType
from ...patrons.api import Patron, current_librarian
from ....modules.utils import extracted_data_from_ref


class LoanOperationLog(OperationLog):
    """Operation log for loans."""

    @classmethod
    def create(cls, data, id_=None, index_refresh='false', **kwargs):
        r"""Create a new record instance and store it in elasticsearch.

        :param loan_data: Dict with the loan metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :param refresh: If `true` then refresh the affected shards to make
            this operation visible to search, if `wait_for` then wait for a
            refresh to make this operation visible to search, if `false`
            (the default) then do nothing with refreshes.
            Valid choices: true, false, wait_for
        :returns: A new :class:`Record` instance.
        """
        log = {
            'record':
            data.dumps(),
            'operation':
            'create',
            'user_name':
            current_librarian.formatted_name
            if current_librarian else 'system',
            'date':
            data['transaction_date'],
            'loan': {
                'override_flag':
                False,
                'transaction_channel':
                'system' if not data.get('selfcheck_terminal_id') else 'sip2',
                'transaction_location_name':
                cls._get_location_name(data['transaction_location_pid']),
                'pickup_location_name':
                cls._get_location_name(data['pickup_location_pid']),
                'patron':
                cls._get_patron_data(data['patron_pid']),
                'item':
                cls._get_item_data(data['item_pid']['value'])
            }
        }

        # Store transaction user name if not done by SIP2
        if log['loan']['transaction_channel'] != 'sip2':
            log['loan']['transaction_user_name'] = cls._get_patron_data(
                data['transaction_user_pid'])['name']

        return super().create(log, index_refresh=index_refresh)

    @classmethod
    def _get_item_data(cls, item_pid):
        """Get item record data.

        :param str item_pid: Item PID
        :returns: Item formatted data
        :rtype: dict
        """
        item = Item.get_record_by_pid(item_pid)
        return {
            'category':
            item['type'],
            'call_number':
            item['call_number'],
            'document':
            cls._get_document_data(
                extracted_data_from_ref(item['document']['$ref'])),
            'holding':
            cls._get_holding_data(
                extracted_data_from_ref(item['holding']['$ref']))
        }

    @classmethod
    def _get_document_data(cls, document_pid):
        """Get document record data.

        :param str document_pid: Document PID
        :returns: Document formatted data
        :rtype: dict
        """
        document = Document.get_record_by_pid(document_pid)
        document = document.dumps()
        return {
            'title':
            document['title'][0]['_text'],
            'type':
            document['type'][0].get('subtype',
                                    document['type'][0]['main_type'])
        }

    @classmethod
    def _get_holding_data(cls, holding_pid):
        """Get holding record data.

        :param str holding_pid: Holding PID
        :returns: Holding formatted data
        :rtype: dict
        """
        holding = Holding.get_record_by_pid(holding_pid)

        return {
            'pid':
            holding['pid'],
            'location_name':
            cls._get_location_name(
                extracted_data_from_ref(holding['location']['$ref']))
        }

    @classmethod
    def _get_location_name(cls, location_pid):
        """Get location name for a location PID.

        :param str location_pid: Location PID
        :returns: Location name
        :rtype: str
        """
        location = Location.get_record_by_pid(location_pid)
        return location['name']

    @classmethod
    def _get_patron_data(cls, patron_pid):
        """Get patron record data.

        :param str patron_pid: Patron PID
        :returns: Patron formatted data
        :rtype: dict
        """
        patron = Patron.get_record_by_pid(patron_pid)

        patron_type = None

        if patron.get('patron'):
            patron_type = PatronType.get_record_by_pid(
                extracted_data_from_ref(patron['patron']['type']['$ref']))

        return {
            'name': patron.formatted_name,
            'type': patron_type['name'] if patron_type else None,
            'birth_date': str(patron.user.profile.birth_date),
            'postal_code': patron.user.profile.postal_code,
            'gender': patron.user.profile.gender or 'other'
        }
