# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""API for manipulating patron_transaction_events."""

from datetime import datetime, timezone
from functools import partial

from flask import current_app

from .models import PatronTransactionEventIdentifier
from ..api import IlsRecord, IlsRecordIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
PatronTransactionEventProvider = type(
    'PatronTransactionEventProvider',
    (Provider,),
    dict(identifier=PatronTransactionEventIdentifier, pid_type='ptre')
)
# minter
patron_transaction_event_id_minter = partial(
    id_minter, provider=PatronTransactionEventProvider)
# fetcher
patron_transaction_event_id_fetcher = partial(
    id_fetcher, provider=PatronTransactionEventProvider)


class PatronTransactionEventsSearch(IlsRecordsSearch):
    """PatronTransactionEventsSearch."""

    class Meta:
        """Search only on patron_transaction_event index."""

        index = 'patron_transaction_events'
        doc_types = None


class PatronTransactionEvent(IlsRecord):
    """PatronTransactionEvent class."""

    minter = patron_transaction_event_id_minter
    fetcher = patron_transaction_event_id_fetcher
    provider = PatronTransactionEventProvider

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, update_parent=True, **kwargs):
        """Create patron transaction event record."""
        if 'creation_date' not in data:
            data['creation_date'] = datetime.now(timezone.utc).isoformat()
        record = super(PatronTransactionEvent, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        if update_parent:
            cls.update_parent_patron_transaction(record)
        return record

    @classmethod
    def create_event_from_patron_transaction(
            cls, patron_transaction=None, dbcommit=None, reindex=None,
            delete_pid=None, update_parent=True):
        """Create a patron transaction event from patron transaction."""
        data = build_patron_transaction_event_ref(patron_transaction, {})
        data['creation_date'] = patron_transaction.get('creation_date')
        record = cls.create(
            data,
            dbcommit=dbcommit,
            reindex=reindex,
            delete_pid=delete_pid,
            update_parent=update_parent
        )
        return record

    def update_parent_patron_transaction(self):
        """Update parent patron transaction amount and status."""
        patron_transaction = self.patron_transaction()
        total_amount = patron_transaction.get('total_amount')
        if self.event_type == 'fee':
            total_amount = total_amount + self.amount
        elif self.event_type in ('payment', 'cancel'):
            total_amount = total_amount - self.amount
        patron_transaction['total_amount'] = total_amount
        if total_amount == 0:
            patron_transaction['status'] = 'closed'

        patron_transaction.update(
            patron_transaction, dbcommit=True, reindex=True)

    def patron_transaction(self):
        """Return the parent patron transaction of the event."""
        from ..patron_transactions.api import PatronTransaction
        return PatronTransaction.get_record_by_pid(self.parent_pid)

    @property
    def parent_pid(self):
        """Return the parent pid of the patron transaction event."""
        return self.replace_refs()['parent']['pid']

    @property
    def event_type(self):
        """Return the type of the patron transaction event."""
        return self.get('type')

    @property
    def amount(self):
        """Return the amount of the patron transaction event."""
        return self.get('amount')

    @property
    def patron_pid(self):
        """Return the patron pid of the patron transaction event."""
        from ..patron_transactions.api import PatronTransaction
        patron_transaction = PatronTransaction.get_record_by_pid(
            self.parent_pid)
        return patron_transaction.patron_pid

    @property
    def organisation_pid(self):
        """Return the organisation pid of the patron transaction event."""
        from ..patron_transactions.api import PatronTransaction
        patron_transaction = PatronTransaction.get_record_by_pid(
            self.parent_pid)
        return patron_transaction.organisation_pid


def build_patron_transaction_event_ref(patron_transaction, data):
    """Create $ref for a patron transaction event."""
    schemas = current_app.config.get('RECORDS_JSON_SCHEMA')
    data_schema = {
        'base_url': current_app.config.get('RERO_ILS_APP_BASE_URL'),
        'schema_endpoint': current_app.config.get('JSONSCHEMAS_ENDPOINT'),
        'schema': schemas['ptre']
    }
    data['$schema'] = '{base_url}{schema_endpoint}{schema}'\
        .format(**data_schema)
    base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
    url_api = '{base_url}/api/{doc_type}/{pid}'
    for record in [
        {
            'resource': 'parent',
            'doc_type': 'patron_transactions',
            'pid': patron_transaction.pid
        }, {
            'resource': 'library',
            'doc_type': 'libraries',
            'pid': patron_transaction.notification_transaction_library_pid
        },
    ]:
        data[record['resource']] = {
            '$ref': url_api.format(
                base_url=base_url,
                doc_type='{}'.format(record['doc_type']),
                pid=record['pid'])
            }
    if patron_transaction.get('type') == 'overdue':
        data['type'] = 'fee'
        data['subtype'] = 'overdue'
        data['amount'] = patron_transaction.get('total_amount')

    return data


class PatronTransactionEventsIndexer(IlsRecordIndexer):
    """Indexing patron transaction event in Elasticsearch."""

    record_cls = PatronTransactionEvent
