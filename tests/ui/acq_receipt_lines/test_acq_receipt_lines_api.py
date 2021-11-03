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

"""Acquisition receipts line API tests."""

from rero_ils.modules.acq_receipt_lines.models import AcqReceiptLineNoteType


def test_receipt_lines_properties(acq_receipt_fiction_martigny,
                                  acq_receipt_line_1_fiction_martigny,
                                  acq_order_line_fiction_martigny,
                                  lib_martigny, acq_account_fiction_martigny):
    """Test receipt line properties."""
    acrl1 = acq_receipt_line_1_fiction_martigny
    # LIBRARY------------------------------------------------------------------
    assert acrl1.library_pid == acq_receipt_fiction_martigny.library_pid
    # ORGANISATION ------------------------------------------------------------
    assert acrl1.organisation_pid == lib_martigny.organisation_pid
    # ORDER LINE --------------------------------------------------------------
    assert acrl1.order_line_pid == acq_order_line_fiction_martigny.pid
    # NOTE --------------------------------------------------------------------
    assert acrl1.get_note(AcqReceiptLineNoteType.STAFF)
    # ACQ ACCOUNT -------------------------------------------------------------
    assert acq_account_fiction_martigny.expenditure_amount == (1001.0, 0.0)
