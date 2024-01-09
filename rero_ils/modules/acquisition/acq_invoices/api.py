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

"""API for manipulating acq_invoices."""

from functools import partial

from rero_ils.modules.acquisition.api import AcquisitionIlsRecord
from rero_ils.modules.api import IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, get_base_url

from .models import AcquisitionInvoiceIdentifier, AcquisitionInvoiceMetadata

# provider
AcquisitionInvoiceProvider = type(
    'AcqInvoiceProvider',
    (Provider,),
    dict(identifier=AcquisitionInvoiceIdentifier, pid_type='acin')
)
# minter
acq_invoice_id_minter = partial(id_minter, provider=AcquisitionInvoiceProvider)
# fetcher
acq_invoice_id_fetcher = partial(
    id_fetcher, provider=AcquisitionInvoiceProvider)


class AcquisitionInvoicesSearch(IlsRecordsSearch):
    """AcquisitionInvoicesSearch."""

    class Meta:
        """Search only on acq_invoice index."""

        index = 'acq_invoices'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class AcquisitionInvoice(AcquisitionIlsRecord):
    """AcquisitionInvoice class."""

    minter = acq_invoice_id_minter
    fetcher = acq_invoice_id_fetcher
    provider = AcquisitionInvoiceProvider
    model_cls = AcquisitionInvoiceMetadata
    pids_exist_check = {
        'required': {
            'lib': 'library',
            'vndr': 'vendor'
        },
        'not_required': {
            'org': 'organisation'
        }
    }

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create acquisition invoice record."""
        cls._acquisition_invoice_build_org_ref(data)
        cls._build_total_amount_of_invoice(data)
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        return record

    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update Acquisition Invoice record."""
        self._build_total_amount_of_invoice(data)
        super().update(data, commit, dbcommit, reindex)
        return self

    @classmethod
    def _build_total_amount_of_invoice(cls, data):
        """Build total amount for invoice."""
        invoice_price = 0
        for idx, item in enumerate(data.get('invoice_items')):
            # build total price for each invoice line item
            invoiceLine = InvoiceLine(item)
            data['invoice_items'][idx]['total_price'] = invoiceLine.total_price
            invoice_price += data['invoice_items'][idx]['total_price']

        # check if discount percentage
        if data.get('discount', {}).get('percentage'):
            invoice_price -= cls._calculate_percentage_discount(
                invoice_price, data.get('discount').get('percentage'))
        # check if discount amount
        if data.get('discount', {}).get('amount'):
            invoice_price -= data.get('discount').get('amount')
        # set invoice price
        data['invoice_price'] = invoice_price

    @classmethod
    def _calculate_percentage_discount(cls, amount, percentage):
        """Calculate discount percentage of invoice."""
        return amount * percentage / 100

    @classmethod
    def _acquisition_invoice_build_org_ref(cls, data):
        """Build $ref for the organisation of the acquisition invoice."""
        library_pid = data.get('library', {}).get('pid')
        if not library_pid:
            library_pid = data.get('library').get(
                '$ref').split('libraries/')[1]
        org_pid = Library.get_record_by_pid(library_pid).organisation_pid \
            or cls.organisation_pid
        data['organisation'] = {
            '$ref': f'{get_base_url()}/api/organisations/{org_pid}'
        }

    @property
    def organisation_pid(self):
        """Shortcut for acquisition invoice organisation pid."""
        return extracted_data_from_ref(self.get('organisation'))

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return extracted_data_from_ref(self.get('library'))

    @property
    def vendor_pid(self):
        """Shortcut for acquisition order vendor pid."""
        return extracted_data_from_ref(self.get('vendor'))

    @property
    def is_active(self):
        """Check if the invoice should be considered as active."""
        # TODO: implement this when introducing the invoicing module
        return True


class AcquisitionInvoicesIndexer(IlsRecordsIndexer):
    """Indexing invoices in Elasticsearch."""

    record_cls = AcquisitionInvoice

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='acin')


class InvoiceLine(object):
    """Acquisition Invoice line class."""

    def __init__(self, data):
        """Initialize instance with dictionary data."""
        self.data = data

    @property
    def total_price(self):
        """Build total price for invoice line."""
        total_price = self.data['price'] * self.data['quantity']
        total_price -= self.data.get('discount', 0)
        return total_price
