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

"""API for manipulating acq_invoices."""

from functools import partial

from .models import AcquisitionInvoiceIdentifier, AcquisitionInvoiceMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..minters import id_minter
from ..providers import Provider
from ..utils import get_base_url

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


class AcquisitionInvoice(IlsRecord):
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

    def update(self, data, dbcommit=True, reindex=True):
        """Update Acquisition Invoice record."""
        self._build_total_amount_of_invoice(data)
        super().update(data, dbcommit, reindex)
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
        org_pid = Library.get_record_by_pid(library_pid).organisation_pid
        url_api = '{base_url}/api/{doc_type}/{pid}'
        org_ref = {
            '$ref': url_api.format(
                base_url=get_base_url(),
                doc_type='organisations',
                pid=org_pid or cls.organisation_pid)
        }
        data['organisation'] = org_ref

    @property
    def organisation_pid(self):
        """Shortcut for acquisition invoice organisation pid."""
        return self.replace_refs().get('organisation').get('pid')

    @property
    def library_pid(self):
        """Shortcut for acquisition order library pid."""
        return self.replace_refs().get('library').get('pid')

    @property
    def vendor_pid(self):
        """Shortcut for acquisition order vendor pid."""
        return self.replace_refs().get('vendor').get('pid')


class AcquisitionInvoicesIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

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
