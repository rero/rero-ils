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

"""Vendors API tests."""
from rero_ils.modules.vendors.models import VendorNoteType


def test_vendors_properties(vendor_martigny, vendor_sion):
    """Test order properties."""

    # NOTES -------------------------------------------------------------------
    assert vendor_martigny.get_note(VendorNoteType.CLAIM) is not None
    assert vendor_martigny.get_note(VendorNoteType.GENERAL) is None
    assert vendor_sion.get_note(VendorNoteType.RECEIPT) is not None
