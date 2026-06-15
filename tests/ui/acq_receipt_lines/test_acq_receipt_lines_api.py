# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipts line API tests."""

from rero_ils.modules.acquisition.acq_receipt_lines.models import AcqReceiptLineNoteType


def test_receipt_lines_properties(
    acq_receipt_fiction_martigny,
    acq_receipt_line_1_fiction_martigny,
    acq_order_line_fiction_martigny,
    lib_martigny,
    acq_account_fiction_martigny,
):
    """Test receipt line properties."""
    acrl1 = acq_receipt_line_1_fiction_martigny
    acre = acq_receipt_fiction_martigny
    # LIBRARY------------------------------------------------------------------
    assert acrl1.library_pid == acq_receipt_fiction_martigny.library_pid
    # ORGANISATION ------------------------------------------------------------
    assert acrl1.organisation_pid == lib_martigny.organisation_pid
    # ORDER LINE --------------------------------------------------------------
    assert acrl1.order_line_pid == acq_order_line_fiction_martigny.pid
    acol = acq_order_line_fiction_martigny

    # NOTE --------------------------------------------------------------------
    assert acrl1.get_note(AcqReceiptLineNoteType.STAFF)
    # ACQ ACCOUNT -------------------------------------------------------------
    assert acq_account_fiction_martigny.expenditure_amount == (1001.0, 0.0)

    # TOTAL AMOUNT ------------------------------------------------------------
    #   The receipt line total amount has multiple variables : quantity,
    #   amount, exchange rate and VAT rate
    #   Starting situation is : qte=1, amount=1000, vat=0, exchange=0
    assert acrl1.total_amount == 1000
    acrl1["vat_rate"] = 6.2  # 1000 * 0.062 --> 62
    assert acrl1.total_amount == 1062
    acrl1["vat_rate"] = 100  # 1000 * 1.00 --> 1000
    assert acrl1.total_amount == 2000
