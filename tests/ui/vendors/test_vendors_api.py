# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
        "type": VendorContactType.SERIAL,
        "city": "Berne",
        "email": "serial@berne.ch",
    }
    vendor_martigny["contacts"].append(serial_info)
    assert not vendor_martigny.get_contact(VendorContactType.ORDER)
    assert vendor_martigny.get_contact(VendorContactType.SERIAL) == serial_info

    # ORDER EMAIL -------------------------------------------------------------
    #   With no specific ORDER contact type, the default contact email field
    #   should be returned
    assert vendor_martigny.order_email == vendor_martigny.get_contact(VendorContactType.DEFAULT).get("email")
