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

import hashlib

from invenio_search import RecordsSearch

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
        """Create a new record instance and store it in elasticsearch.

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
            'record': {
                'value': data.get('pid'),
                'type': 'loan'
            },
            'operation': 'create',
            'date': data['transaction_date'],
            'loan': {
                'pid': data['pid'],
                'trigger': data['trigger'],
                'override_flag': False,
                'transaction_channel': 'system' if not data.get(
                    'selfcheck_terminal_id') else 'sip2',
                'transaction_location': {
                    'pid': data['transaction_location_pid'],
                    'name': cls._get_location_name(
                        data['transaction_location_pid'])
                },
                'pickup_location': {
                    'pid': data['pickup_location_pid'],
                    'name': cls._get_location_name(data['pickup_location_pid'])
                },
                'patron':
                cls._get_patron_data(data['patron_pid']),
                'item':
                cls._get_item_data(data['item_pid']['value'])
            }
        }
        if current_librarian:
            log['user'] = {
                'type': 'ptrn',
                'value': current_librarian.pid
            }
            log['user_name'] = current_librarian.formatted_name
            log['organisation'] = {
                'value': current_librarian.organisation_pid,
                'type': 'org'
            }
            log['library'] = {
                'value': current_librarian.library_pid,
                'type': 'lib'
            }
        else:
            log['user_name'] = 'system'
        # Store transaction user name if not done by SIP2
        if log['loan']['transaction_channel'] != 'sip2':
            log['loan']['transaction_user'] = {
                'pid': data['transaction_user_pid'],
                'name': cls._get_patron_data(
                    data['transaction_user_pid'])['name']
            }
        return super().create(log, index_refresh=index_refresh)

    @classmethod
    def _get_item_data(cls, item_pid):
        """Get item record data.

        :param str item_pid: Item PID
        :returns: Item formatted data
        :rtype: dict
        """
        item = Item.get_record_by_pid(item_pid)
        data = {
            'pid': item.pid,
            'library_pid': item.library_pid,
            'category': item['type'],
            'document': cls._get_document_data(
                extracted_data_from_ref(item['document']['$ref'])),
            'holding': cls._get_holding_data(
                extracted_data_from_ref(item['holding']['$ref']))
        }
        if item.get('call_number'):
            data['call_number'] = item.get('call_number')
        if item.get('enumerationAndChronology'):
            data['enumerationAndChronology'] =\
                item.get('enumerationAndChronology')
        return data

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
            'pid': document['pid'],
            'title': next(filter(lambda x: x.get('type') == 'bf:Title',
                                 document.get('title'))
                          ).get('_text'),
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
            'pid': holding.pid,
            'location_name': cls._get_location_name(
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

        hashed_pid = hashlib.md5(patron.pid.encode()).hexdigest()
        data = {
            'name': patron.formatted_name,
            'type': patron_type['name'] if patron_type else None,
            'age': patron.age,
            'postal_code': patron.user.profile.postal_code,
            'gender': patron.user.profile.gender or 'no_information',
            'pid': patron.pid,
            'hashed_pid': hashed_pid
        }

        if patron.get('local_codes'):
            data['local_codes'] = patron['local_codes']

        return data

    @classmethod
    def get_logs_by_record_pid(cls, pid):
        """Get all logs for a given record PID.

        :param str pid: record PID.
        :returns: List of logs.
        :rtype: list
        """
        return list(
            RecordsSearch(index=cls.index_name).filter(
                'bool', must={
                    'exists': {
                        'field': 'loan'
                    }
                }).filter('term', record__value=pid).scan())

    @classmethod
    def anonymize_logs(cls, loan_pid):
        """Anonymize all logs corresponding to the given loan.

        :param loan_pid: Loan PID.
        """
        for log in cls.get_logs_by_record_pid(loan_pid):
            record = log.to_dict()
            record['loan']['patron'].pop('name', None)
            record['loan']['patron'].pop('pid', None)
            cls.update(log.meta.id, log['date'], record)
