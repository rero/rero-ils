# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition invoice record mapping tests."""

from rero_ils.modules.acquisition.acq_orders.api import AcqOrder, AcqOrdersSearch
from tests.utils import get_mapping


def test_acq_orders_search_mapping(search, db, lib_martigny, vendor_martigny, acq_order_fiction_martigny_data):
    """Test acquisition orders search index mapping."""
    search = AcqOrdersSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    invoice = AcqOrder.create(acq_order_fiction_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    invoice.delete(force=True, dbcommit=True, delindex=True)
