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

"""API for manipulating Acquisition Receipt Lines."""

from copy import deepcopy
from functools import partial

from werkzeug.utils import cached_property

from rero_ils.modules.acquisition.api import AcquisitionIlsRecord
from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, get_ref_for_pid

from .extensions import AcqReceiptLineValidationExtension, \
    AcquisitionReceiptLineCompleteDataExtension
from .models import AcqReceiptLineIdentifier, AcqReceiptLineMetadata

# provider
AcqReceiptLineProvider = type(
    'AcqReceiptLineProvider',
    (Provider,),
    dict(identifier=AcqReceiptLineIdentifier, pid_type='acrl')
)
# minter
acq_receipt_line_id_minter = partial(
    id_minter, provider=AcqReceiptLineProvider)
# fetcher
acq_receipt_line_id_fetcher = partial(
    id_fetcher, provider=AcqReceiptLineProvider)


class AcqReceiptLinesSearch(IlsRecordsSearch):
    """Acquisition Receipt Lines Search."""

    class Meta:
        """Search only on acq_receipt_lines index."""

        index = 'acq_receipt_lines'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcqReceiptLine(AcquisitionIlsRecord):
    """AcqReceiptLine class."""

    minter = acq_receipt_line_id_minter
    fetcher = acq_receipt_line_id_fetcher
    provider = AcqReceiptLineProvider
    model_cls = AcqReceiptLineMetadata

    _extensions = [
        AcquisitionReceiptLineCompleteDataExtension(),
        AcqReceiptLineValidationExtension()
    ]

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition Receipt Line record."""
        # TODO : should be used into `pre_create` hook extensions but seems not
        #        work as expected.
        cls._build_additional_refs(data)
        return super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)

    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update Acquisition Receipt Line record."""
        # TODO :: try to find a better way to load original record.
        original_record = self.__class__.get_record(self.id)

        new_data = deepcopy(dict(self))
        new_data.update(data)
        self._build_additional_refs(new_data)
        super().update(new_data, commit, dbcommit, reindex)

        return self

    @classmethod
    def _build_additional_refs(cls, data):
        """Build $ref for the organisation and library the acq receipt line."""
        receipt = extracted_data_from_ref(
            data.get('acq_receipt'), data='record')
        if receipt:
            data['organisation'] = {
                '$ref': get_ref_for_pid('org', receipt.organisation_pid)
            }
            data['library'] = {
                '$ref': get_ref_for_pid('lib', receipt.library_pid)
            }

    # GETTER & SETTER =========================================================
    #   * Define some properties as shortcut to quickly access object attrs.
    #   * Defines some getter methods to access specific object values.
    @cached_property
    def receipt(self):
        """Shortcut to the receipt of the receipt line."""
        return extracted_data_from_ref(self.get('acq_receipt'), data='record')

    @property
    def library_pid(self):
        """Shortcut for acquisition receipt line library pid."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def order_line_pid(self):
        """Shortcut for related acquisition order line pid."""
        return extracted_data_from_ref(self.get('acq_order_line'))

    @cached_property
    def order_line(self):
        """Shortcut for related acquisition order line record."""
        return extracted_data_from_ref(
            self.get('acq_order_line'),
            data='record'
        )

    @property
    def is_active(self):
        """Check if the receipt line should be considered as active.

        To know if an receipt line is active, we need to check the related
        budget. This budget has an 'is_active' field.
        """
        return self.order_line.is_active

    @property
    def acq_account_pid(self):
        """Shortcut for related acquisition account pid."""
        return self.order_line.account

    @property
    def receipt_pid(self):
        """Shortcut for related acquisition receipt pid."""
        return extracted_data_from_ref(self.get('acq_receipt'))

    @property
    def amount(self):
        """Shortcut for related acquisition amount."""
        return self.get('amount')

    @property
    def total_amount(self):
        """Shortcut for related acquisition total_amount."""
        vat_factor = (100 + self.get('vat_rate', 0)) / 100
        total = self.amount * self.receipt.exchange_rate * self.quantity * \
            vat_factor
        return round(total, 2)

    @property
    def quantity(self):
        """Shortcut for related acquisition quantity."""
        return self.get('quantity')

    @property
    def organisation_pid(self):
        """Get organisation pid for acquisition receipt line."""
        return self.receipt.organisation_pid

    def get_note(self, note_type):
        """Get a specific type of note.

        Only one note of each type could be created.
        :param note_type: the note type to filter as
        `AcqReceiptLineNoteType` value.
        :return the note content if exists, otherwise returns None.
        """
        note = [
            note.get('content') for note in self.get('notes', [])
            if note.get('type') == note_type
        ]
        return next(iter(note), None)

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        # Note: not possible to delete records attached to rolled_over budget.
        if not self.is_active:
            cannot_delete['links'] = {'rolled_over': True}
        return cannot_delete


class AcqReceiptLinesIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = AcqReceiptLine

    def index(self, record):
        """Index an AcqReceiptLine line record."""
        return_value = super().index(record)
        # The reindexing of the parent receipt will also fired the
        # indexing of the parent order and related account
        # TODO :: try to find a way to not reindex multiple times the order,
        #         then the account
        record.receipt.reindex()
        record.order_line.reindex()
        return return_value

    def delete(self, record):
        """Delete an AcqReceiptLine record from indexer."""
        return_value = super().delete(record)
        record.receipt.reindex()
        record.order_line.reindex()
        return return_value
