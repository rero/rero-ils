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

"""API for manipulating vendors."""

from functools import partial

from .models import VendorIdentifier, VendorMetadata
from ..acq_invoices.api import AcquisitionInvoicesSearch
from ..acq_orders.api import AcqOrdersSearch
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import sorted_pids

# provider
VendorProvider = type(
    'VendorProvider',
    (Provider,),
    dict(identifier=VendorIdentifier, pid_type='vndr')
)
# minter
vendor_id_minter = partial(id_minter, provider=VendorProvider)
# fetcher
vendor_id_fetcher = partial(id_fetcher, provider=VendorProvider)


class VendorsSearch(IlsRecordsSearch):
    """VendorsSearch."""

    class Meta:
        """Search only on vendor index."""

        index = 'vendors'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Vendor(IlsRecord):
    """Vendor class."""

    minter = vendor_id_minter
    fetcher = vendor_id_fetcher
    provider = VendorProvider
    model_cls = VendorMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation'
        }
    }

    @property
    def order_email(self):
        """Shortcut for vendor order email.

        :return the best possible email to use for this vendor. If the specific
                order contact information does not exist, the default contact
                information will be used.
        """
        return self\
            .get('order_contact', self.get('default_contact', {}))\
            .get('email')

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        from rero_ils.modules.holdings.api import HoldingsSearch
        acq_orders_query = AcqOrdersSearch()\
            .filter('term', vendor__pid=self.pid)
        acq_invoices_query = AcquisitionInvoicesSearch()\
            .filter('term', vendor__pid=self.pid)
        hold_query = HoldingsSearch()\
            .filter('term', vendor__pid=self.pid)
        links = {}
        if get_pids:
            acq_orders = sorted_pids(acq_orders_query)
            acq_invoices = sorted_pids(acq_invoices_query)
            holdings = sorted_pids(hold_query)
        else:
            acq_orders = acq_orders_query.count()
            acq_invoices = acq_invoices_query.count()
            holdings = hold_query.count()
        if acq_orders:
            links['acq_orders'] = acq_orders
        if acq_invoices:
            links['acq_invoices'] = acq_invoices
        if holdings:
            links['holdings'] = holdings
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete


class VendorsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Vendor

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='vndr')
