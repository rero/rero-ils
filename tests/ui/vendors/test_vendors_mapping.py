# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition vendors record mapping tests."""

from rero_ils.modules.vendors.api import Vendor, VendorsSearch
from tests.utils import get_mapping


def test_vendors_search_mapping(search, db, org_martigny, vendor_martigny_data):
    """Test vendors search index mapping."""
    search = VendorsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    vendor = Vendor.create(vendor_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    vendor.delete(force=True, dbcommit=True, delindex=True)
