# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipt line record mapping tests."""

from rero_ils.modules.acquisition.acq_receipt_lines.api import (
    AcqReceiptLine,
    AcqReceiptLinesSearch,
)
from tests.utils import get_mapping


def test_acq_receipt_lines_search_mapping(
    search,
    db,
    lib_martigny,
    vendor_martigny,
    acq_receipt_line_1_fiction_martigny,
    acq_receipt_line_1_fiction_martigny_data,
):
    """Test acquisition receipt lines search index mapping."""
    search = AcqReceiptLinesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    receipt = AcqReceiptLine.create(
        acq_receipt_line_1_fiction_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True,
    )
    assert mapping == get_mapping(search.Meta.index)
    receipt.delete(force=True, dbcommit=True, delindex=True)
