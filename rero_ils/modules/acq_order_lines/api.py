# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""API for manipulating Acquisition Order Line."""

from copy import deepcopy
from functools import partial

from flask_babelex import gettext as _

from .extensions import AcqOrderLineValidationExtension
from .models import AcqOrderLineIdentifier, AcqOrderLineMetadata, \
    AcqOrderLineStatus
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import extracted_data_from_ref, get_ref_for_pid

# provider
AcqOrderLineProvider = type(
    'AcqOrderLineProvider',
    (Provider,),
    dict(identifier=AcqOrderLineIdentifier, pid_type='acol')
)
# minter
acq_order_line_id_minter = partial(id_minter, provider=AcqOrderLineProvider)
# fetcher
acq_order_line_id_fetcher = partial(id_fetcher, provider=AcqOrderLineProvider)


class AcqOrderLinesSearch(IlsRecordsSearch):
    """Acquisition Order Line Search."""

    class Meta:
        """Search only on Acquisition Order Line index."""

        index = 'acq_order_lines'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcqOrderLine(IlsRecord):
    """Acquisition Order Line class."""

    minter = acq_order_line_id_minter
    fetcher = acq_order_line_id_fetcher
    provider = AcqOrderLineProvider
    model_cls = AcqOrderLineMetadata
    pids_exist_check = {
        'required': {
            'doc': 'document',
            'acac': 'acq_account',
            'acor': 'acq_order'
        },
        'not_required': {
            'org': 'organisation'
        }
    }

    _extensions = [
        AcqOrderLineValidationExtension()
    ]

    # API METHODS =============================================================
    #   Overriding the `IlsRecord` default behavior for create and update
    #   Invenio API methods.

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        :return: False if
            - notes array has multiple notes with same type
        """
        # NOTES fields testing
        note_types = [note.get('type') for note in self.get('notes', [])]
        if len(note_types) != len(set(note_types)):
            return _('Can not have multiple notes of same type.')

        return True

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition Order Line record."""
        # TODO : should be used into `pre_create` hook extensions but seems not
        #        work as expected.
        cls._build_additional_refs(data)
        cls._build_total_amount(data)
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update Acquisition Order Line record."""
        # TODO :: try to find a better way to load original record.
        original_record = self.__class__.get_record_by_id(self.id)

        new_data = deepcopy(dict(self))
        new_data.update(data)
        self._build_additional_refs(new_data)
        self._build_total_amount(new_data)
        super().update(new_data, commit, dbcommit, reindex)

        # If the related account change, then we need to reindex the original
        # account to release encumbrance amount on this account.
        if original_record.account_pid != self.account_pid:
            original_record.account.reindex()

        return self

    @classmethod
    def _build_additional_refs(cls, data):
        """Build $ref for the organisation of the acquisition order."""
        order = extracted_data_from_ref(data.get('acq_order'), data='record')
        if order:
            data['library'] = {
                '$ref': get_ref_for_pid('lib', order.library_pid)
            }
            data['organisation'] = {
                '$ref': get_ref_for_pid('org', order.organisation_pid)
            }

    @classmethod
    def _build_total_amount(cls, data):
        """Build total amount for order line."""
        data['total_amount'] = data['amount'] * data['quantity']

    # GETTER & SETTER =========================================================
    #   * Define some properties as shortcut to quickly access object attrs.
    #   * Defines some getter methods to access specific object values.

    @property
    def order_pid(self):
        """Shortcut for acquisition order pid."""
        return extracted_data_from_ref(self.get('acq_order'))

    @property
    def order(self):
        """Shortcut to the order of the order line."""
        return extracted_data_from_ref(self.get('acq_order'), data='record')

    @property
    def order_date(self):
        """Shortcut for acquisition order send date."""
        return self.get('order_date')

    @property
    def is_cancelled(self):
        """Shortcut for acquisition order is_cancelled falg."""
        return self.get('is_cancelled')

    @property
    def account_pid(self):
        """Shortcut to the account pid related to this order line."""
        return extracted_data_from_ref(self.get('acq_account'))

    @property
    def account(self):
        """Shortcut to the account object related to this order line."""
        return extracted_data_from_ref(self.get('acq_account'), data='record')

    @property
    def document(self):
        """Shortcut to the document object related to this order line."""
        return extracted_data_from_ref(self.get('document'), data='record')

    @property
    def organisation_pid(self):
        """Get organisation pid for acquisition order."""
        return self.order.organisation_pid

    @property
    def quantity(self):
        """Get quantity of ordered_items for a line order.

        This comes from the metadata of the order line that represent the
        number of items to order or already ordered.
        """
        return self.get('quantity')

    @property
    def received_quantity(self):
        """Get quantity of received ordered_items for a line order.

        The received quantitiy is number of quantity received for the resource
        acq_receipt_line and for the correspoding acq_line_order.
        """
        from rero_ils.modules.acq_receipt_lines.api import \
            AcqReceiptLinesSearch
        search = AcqReceiptLinesSearch()\
            .filter('term', acq_order_line__pid=self.pid)
        search.aggs.metric('sum_order_line_recieved', 'sum', field='quantity')
        results = search.execute()
        return results.aggregations.sum_order_line_recieved.value

    @property
    def unreceived_quantity(self):
        """Get quantity of unreceived ordered_items for a line order."""
        return self.quantity - self.received_quantity

    @property
    def status(self):
        """Calculate the order line status.

        The status of the order line is saved only in the elasticsearch index
        and it is calculated based on the following roles:
        * at the creation, the order line receives the `APPROVED` status
        * if field `is_cancelled` is checked, it receives the `CANCELLED`status
        * if some items are received but not the total, it receives
            `PARTIALLY_RECEIVED` status
        * if all items are received, it receives `RECEIVED` status
        """
        if self.is_cancelled:
            return AcqOrderLineStatus.CANCELLED
        status = AcqOrderLineStatus.ORDERED \
            if self.order_date else AcqOrderLineStatus.APPROVED
        received_quantity = self.received_quantity
        # not use the property to prevent an extra ES call
        unreceived_quantity = self.quantity - received_quantity
        if unreceived_quantity == 0:  # fully received
            status = AcqOrderLineStatus.RECEIVED
        elif unreceived_quantity and unreceived_quantity != self.quantity:
            status = AcqOrderLineStatus.PARTIALLY_RECEIVED
        return status

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return self.order.library_pid

    def get_note(self, note_type):
        """Get a specific type of note.

        Only one note of each type could be created.
        :param note_type: the note type to filter as `OrderLineNoteType` value.
        :return the note content if exists, otherwise returns None.
        """
        note = [
            note.get('content') for note in self.get('notes', [])
            if note.get('type') == note_type
        ]
        return next(iter(note), None)


class AcqOrderLinesIndexer(IlsRecordsIndexer):
    """Indexing Acquisition Order Line in Elasticsearch."""

    record_cls = AcqOrderLine

    def index(self, record):
        """Index an Acquisition Order Line and update total amount of order."""
        from ..acq_orders.api import AcqOrder
        return_value = super().index(record)
        order = AcqOrder.get_record_by_pid(record.order_pid)
        order.reindex()
        record.account.reindex()
        return return_value

    def delete(self, record):
        """Delete a Acquisition Order Line and update total amount of order."""
        from ..acq_orders.api import AcqOrder
        return_value = super().delete(record)
        order = AcqOrder.get_record_by_pid(record.order_pid)
        order.reindex()
        record.account.reindex()
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='acol')
