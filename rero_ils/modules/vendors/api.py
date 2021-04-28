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

        if the order email does not exist, it returns the default contact email
        """
        return self.get(
            'order_contact', self.get('default_contact', {})
        ).get('email')

    def count_links_to_me(self, search_class):
        """Get number of acquisition orders."""
        return search_class()\
            .filter('term', vendor__pid=self.pid)\
            .source().count()

    def get_links_to_me(self):
        """Get number of links."""
        from rero_ils.modules.holdings.api import HoldingsSearch
        links = {
            'acq_orders': self.count_links_to_me(AcqOrdersSearch),
            'acq_invoices': self.count_links_to_me(AcquisitionInvoicesSearch),
            'holdings': self.count_links_to_me(HoldingsSearch),
        }
        links = {k: v for k, v in links.items() if v}
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
