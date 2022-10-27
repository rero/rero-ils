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

"""API for manipulating Acquisition Receipts."""

from copy import deepcopy
from functools import partial

from rero_ils.modules.acquisition.acq_receipt_lines.api import \
    AcqReceiptLine, AcqReceiptLinesSearch
from rero_ils.modules.acquisition.api import AcquisitionIlsRecord
from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.extensions import DecimalAmountExtension
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, get_objects, \
    get_ref_for_pid, sorted_pids

from .extensions import AcqReceiptExtension, \
    AcquisitionReceiptCompleteDataExtension
from .models import AcqReceiptIdentifier, AcqReceiptLineCreationStatus, \
    AcqReceiptMetadata

# provider
AcqReceiptProvider = type(
    'AcqReceiptProvider',
    (Provider,),
    dict(identifier=AcqReceiptIdentifier, pid_type='acre')
)
# minter
acq_receipt_id_minter = partial(id_minter, provider=AcqReceiptProvider)
# fetcher
acq_receipt_id_fetcher = partial(id_fetcher, provider=AcqReceiptProvider)


class AcqReceiptsSearch(IlsRecordsSearch):
    """Acquisition Receipts Search."""

    class Meta:
        """Search only on acq_order index."""

        index = 'acq_receipts'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcqReceipt(AcquisitionIlsRecord):
    """AcqReceipt class."""

    minter = acq_receipt_id_minter
    fetcher = acq_receipt_id_fetcher
    provider = AcqReceiptProvider
    model_cls = AcqReceiptMetadata

    _extensions = [
        AcqReceiptExtension(),
        AcquisitionReceiptCompleteDataExtension(),
        DecimalAmountExtension(
            callback=lambda rec:
                [adj['amount'] for adj in rec.get('amount_adjustments', [])]
        ),
    ]

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition receipt record.

        :param data: a dict data to create the record.
        :param dbcommit: if True call dbcommit, make the change effective
                         in db.
        :param reindex: reindex the record.
        :param id_ - UUID, it would be generated if it is not given
        :param delete_pid - remove the pid present in the data if True
        :returns: the created record
        """
        cls._build_additional_refs(data)
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        # reindex the related account if necessary
        if reindex:
            for account in record.get_adjustment_accounts():
                account.reindex()
        return record

    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update Acquisition receipt Line record.

        :param data: a dict data to create the record.
        :param commit: if True push the db transaction.
        :param dbcommit: if True call dbcommit, make the change effective
                         in db.
        :param reindex: reindex the record.
        :returns: the updated record
        """
        # We need to manage the indexing of related adjustment accounts to
        # ensure than expenditure amount of theses accounts are correct. To do
        # that, we need to get the accounts BEFORE changes and AFTER changes (
        # in the case of we delete adjustment) to create a python set. Each
        # entry of this set should be reindex.

        original_accounts = self.get_adjustment_accounts()
        new_data = deepcopy(dict(self))
        new_data.update(data)
        self._build_additional_refs(new_data)
        record = super().update(new_data, commit, dbcommit, reindex)
        if reindex:
            AcqReceiptsSearch().flush_and_refresh()
        new_accounts = record.get_adjustment_accounts()
        accounts_set = original_accounts.union(new_accounts)
        for account in accounts_set:
            account.reindex()
        return self

    @classmethod
    def _build_additional_refs(cls, data):
        """Build $ref for the organisation of the acquisition receipt."""
        order = extracted_data_from_ref(data.get('acq_order'), data='record')
        if order:
            data['library'] = {
                '$ref': get_ref_for_pid('lib', order.library_pid)
            }
            data['organisation'] = {
                '$ref': get_ref_for_pid('org', order.organisation_pid)
            }

    def create_receipt_lines(self, receipt_lines=None, dbcommit=True,
                             reindex=True):
        """Create multiple receipt lines.

        :param receipt_lines: a list of dicts to create the records.
        :param dbcommit: if True call dbcommit, make the change effective
                         in db.
        :param reindex: reindex the record.
        :returns: a list containing the given data to build the receipt line
                  with a `status` field, either `success` or `failure`.
                  In case of `success`, the created record is returned.
                  In case `failure`, the reason is given in a field `error`
        """
        created_receipt_lines = []
        receipt_lines = receipt_lines or []
        for receipt_line in receipt_lines:
            record = {
                'data': receipt_line,
                'status': AcqReceiptLineCreationStatus.SUCCESS
            }
            receipt_line['acq_receipt'] = {
                '$ref': get_ref_for_pid('acre', self.pid)
            }
            try:
                line = AcqReceiptLine.create(receipt_line, dbcommit=dbcommit,
                                             reindex=reindex)
                record['receipt_line'] = line
            except Exception as error:
                record['status'] = AcqReceiptLineCreationStatus.FAILURE
                record['error_message'] = str(error)
            created_receipt_lines.append(record)

        return created_receipt_lines

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        from ..acq_receipt_lines.api import AcqReceiptLinesSearch
        links = {}
        receipt_lines_query = AcqReceiptLinesSearch() \
            .filter('term', acq_receipt__pid=self.pid)
        if get_pids:
            acq_receipt_lines = sorted_pids(receipt_lines_query)
        else:
            acq_receipt_lines = receipt_lines_query.count()

        if acq_receipt_lines:
            links['acq_receipt_lines'] = acq_receipt_lines
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete receipt."""
        cannot_delete = {}
        # Note: not possible to delete records attached to rolled_over budget.
        if not self.is_active:
            cannot_delete['links'] = {'rolled_over': True}
            return cannot_delete
        # Note : linked receipt lines aren't yet a reason to keep the record.
        #        These lines will be deleted with the record.
        # TODO :: add a reason if order is concluded (rollovered or invoiced)
        return cannot_delete

    # GETTER & SETTER =========================================================
    #   * Define some properties as shortcut to quickly access object attrs.
    #   * Defines some getter methods to access specific object values.

    @property
    def order_pid(self):
        """Shortcut for related acquisition order pid."""
        return extracted_data_from_ref(self.get('acq_order'))

    @property
    def order(self):
        """Shortcut to the related order."""
        return extracted_data_from_ref(self.get('acq_order'), data='record')

    @property
    def is_active(self):
        """Check if the receipt should be considered as active.

        To know if an receipt is active, we need to check the related
        budget. This budget has an 'is_active' field.
        """
        return self.order.is_active

    @property
    def amount_adjustments(self):
        """Shortcut to get receipt amount adjustments."""
        return self.get('amount_adjustments', [])

    @property
    def exchange_rate(self):
        """Shortcut to get receipt exchange_rate."""
        return self.get('exchange_rate')

    @property
    def total_amount(self):
        """Get this acquisition receipt total amount.

        To compute the total amount, we need to sum:
          * all related receipt lines total amount
          * all additional amount adjustments from the current receipt.

        :return the receipt total amount rounded on 0.01.
        """
        # Compute the total of all related receipt line
        search = AcqReceiptLinesSearch() \
            .filter('term', acq_receipt__pid=self.pid)
        search.aggs.metric(
            'receipt_total_amount',
            'sum',
            field='total_amount',
            script={
                'source': 'Math.round(_value*100)/100.00'
            }
        )
        results = search.execute()
        total = results.aggregations.receipt_total_amount.value
        # Add the sum of all adjustments
        total += sum(fee.get('amount') for fee in self.amount_adjustments)
        return round(total, 2)

    @property
    def total_item_quantity(self):
        """Get the number of items related to this receipt."""
        search = AcqReceiptLinesSearch() \
            .filter('term', acq_receipt__pid=self.pid)
        search.aggs.metric('quantity', 'sum', field='quantity')
        results = search.execute()
        return results.aggregations.quantity.value

    @property
    def library_pid(self):
        """Shortcut for acquisition receipt library pid."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def organisation_pid(self):
        """Shortcut for acquisition receipt organisation pid."""
        return extracted_data_from_ref(self.get('organisation'))

    def get_receipt_lines(self, output=None):
        """Get all receipt lines related to this receipt.

        :param output: output method. 'count', 'pids' or None.
        :return a generator of related order lines (or length).
        """
        query = AcqReceiptLinesSearch()\
            .filter('term', acq_receipt__pid=self.pid)

        if output == 'count':
            return query.count()
        elif output == 'pids':
            return sorted_pids(query)
        else:
            return get_objects(AcqReceiptLine, query)

    def get_note(self, note_type):
        """Get a specific type of note.

        Only one note of each type could be created.
        :param note_type: note type to filter as `AcqReceiptNoteType` value.
        :return the note content if exists, otherwise returns None.
        """
        note = [
            note.get('content') for note in self.get('notes', [])
            if note.get('type') == note_type
        ]
        return next(iter(note), None)

    def get_adjustment_accounts(self):
        """Get the list of adjustment account pid related to this receipt."""
        return set([
            extracted_data_from_ref(adj.get('acq_account'), data='record')
            for adj in self.amount_adjustments
        ])


class AcqReceiptsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = AcqReceipt

    def index(self, record):
        """Index an AcqReceiptLine line record."""
        return_value = super().index(record)
        record.order.reindex()
        return return_value

    def delete(self, record):
        """Delete a AcqReceipt from indexer."""
        super().delete(record)
        record.order.reindex()
        for account in record.get_adjustment_accounts():
            account.reindex()
