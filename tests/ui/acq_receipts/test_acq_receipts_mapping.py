# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipt record mapping tests."""

from unittest import mock

from rero_ils.modules.acquisition.acq_receipts.api import AcqReceipt, AcqReceiptsSearch
from tests.utils import get_mapping


def test_acq_receipts_search_mapping(
    search,
    db,
    lib_martigny,
    vendor_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_account_fiction_martigny,
    acq_receipt_fiction_martigny_data,
):
    """Test acquisition receipts search index mapping."""
    search = AcqReceiptsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    with mock.patch(
        "rero_ils.modules.notifications.dispatcher.Dispatcher.dispatch_notifications",
        mock.MagicMock(return_value={"sent": 1}),
    ):
        acq_order_fiction_martigny.send_order(
            [
                {"type": "to", "address": "ils@foo.com"},
                {"type": "reply_to", "address": "admin@foo.com"},
            ]
        )
    receipt = AcqReceipt.create(acq_receipt_fiction_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    receipt.delete(force=True, dbcommit=True, delindex=True)
