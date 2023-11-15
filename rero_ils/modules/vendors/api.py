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

"""API for manipulating vendors."""

from functools import partial

from flask_babel import gettext as _

from rero_ils.modules.acquisition.acq_invoices.api import \
    AcquisitionInvoicesSearch
from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import sorted_pids

from .models import VendorContactType, VendorIdentifier, VendorMetadata

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

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        :return: False if
            - contacts array has multiple contacts with same type
            - notes array has multiple notes with same type
        """
        # CONTACTS field
        types = [contact.get('type') for contact in self.get('contacts', [])]
        if len(types) != len(set(types)):
            return _('Can not have multiple contacts with the same type.')
        # NOTES field
        types = [note.get('type') for note in self.get('notes', [])]
        if len(types) != len(set(types)):
            return _('Can not have multiple notes with the same type.')

        return True

    def get_contact(self, contact_type):
        """Get contact by type.

        :param contact_type: type of the contact. See `VendorContactType` class
            to see all contact type available.
        :return data relative to this contact type.
        """
        for contact in self.get('contacts', []):
            if contact['type'] == contact_type:
                return contact

    @property
    def order_email(self):
        """Shortcut for vendor order email.

        :return the best possible email to use for this vendor. If the specific
                order contact information does not exist, the default contact
                information will be used.
        """
        contact = \
            self.get_contact(VendorContactType.ORDER) or \
            self.get_contact(VendorContactType.DEFAULT) or \
            {}
        return contact.get('email')

    @property
    def serial_email(self):
        """Shortcut for vendor serial email.

        :return the best possible email to use for this vendor. If the specific
                serial contact information does not exist, the default contact
                information will be used.
        """
        contact = \
            self.get_contact(VendorContactType.SERIAL) or \
            self.get_contact(VendorContactType.DEFAULT) or \
            {}
        return contact.get('email')

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

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        from rero_ils.modules.acquisition.acq_orders.api import AcqOrdersSearch
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
        if links := self.get_links_to_me():
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
