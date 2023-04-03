# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Vendors API tests."""
from rero_ils.modules.vendors.models import VendorContactType, VendorNoteType


def test_vendors_properties(vendor_martigny, vendor_sion):
    """Test vendor properties."""

    # NOTES -------------------------------------------------------------------
    assert vendor_martigny.get_note(VendorNoteType.CLAIM) is not None
    assert vendor_martigny.get_note(VendorNoteType.GENERAL) is None
    assert vendor_sion.get_note(VendorNoteType.RECEIPT) is not None

    # CONTACTS ----------------------------------------------------------------
    serial_info = {
        'type': VendorContactType.SERIAL,
        'city': 'Berne',
        'email': 'serial@berne.ch'
    }
    vendor_martigny['contacts'].append(serial_info)
    assert not vendor_martigny.get_contact(VendorContactType.ORDER)
    assert vendor_martigny.get_contact(VendorContactType.SERIAL) == serial_info

    # ORDER EMAIL -------------------------------------------------------------
    #   With no specific ORDER contact type, the default contact email field
    #   should be returned
    assert vendor_martigny.order_email == \
           vendor_martigny.get_contact(VendorContactType.DEFAULT).get('email')


def test_vendors_get_links_to_me(
    vendor_martigny, acq_invoice_fiction_martigny
):
    """Test vendors relations."""
    links = vendor_martigny.get_links_to_me(True)
    assert acq_invoice_fiction_martigny.pid in links['acq_invoices']
