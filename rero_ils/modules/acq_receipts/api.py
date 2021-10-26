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

"""API for manipulating Acquisition Receipts."""

from copy import deepcopy
from functools import partial

from .models import AcqReceiptIdentifier, AcqReceiptMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import extracted_data_from_ref, get_ref_for_pid

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


class AcqReceipt(IlsRecord):
    """AcqReceipt class."""

    minter = acq_receipt_id_minter
    fetcher = acq_receipt_id_fetcher
    provider = AcqReceiptProvider
    model_cls = AcqReceiptMetadata

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=True, reindex=True, **kwargs):
        """Create Acquisition receipt record.

        :param data: a dict data to create the record.
        :param dbcommit: if True call dbcommit, make the change effective
                         in db.
        :param redindex: reindex the record.
        :param id_ - UUID, it would be generated if it is not given
        :param delete_pid - remove the pid present in the data if True
        :returns: the created record
        """
        cls._build_additional_refs(data)
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update Acquisition receipt Line record.

        :param data: a dict data to create the record.
        :param commit: if True push the db transaction.
        :param dbcommit: if True call dbcommit, make the change effective
                         in db.
        :param redindex: reindex the record.
        :returns: the updated record
        """
        new_data = deepcopy(dict(self))
        new_data.update(data)
        self._build_additional_refs(new_data)
        super().update(new_data, commit, dbcommit, reindex)
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
    def amount_adjustments(self):
        """Shortcut to get receipt amount adjustments."""
        return self.get('amount_adjustments', [])

    @property
    def total_amount(self):
        """Get this acquisition receipt total amount.

        To compute the total amount, we need to sum:
          * all related receipt lines total amount
          * all additional amount adjustments from the current receipt.

        :return the receipt total amount rounded on 0.01.
        """
        # TODO: adapt this method after adding the receipt_lines resource.
        # total = self._get_receipt_lines_total_amount()
        total = sum([fee.get('amount') for fee in self.amount_adjustments])
        return round(total, 2)

    @property
    def library_pid(self):
        """Shortcut for acquisition receipt library pid."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def organisation_pid(self):
        """Shortcut for acquisition receipt organisation pid."""
        return extracted_data_from_ref(self.get('organisation'))

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


class AcqReceiptsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = AcqReceipt
