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

"""Acquisition receipts API tests."""
import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.acquisition.acq_receipts.models import AcqReceiptNoteType
from rero_ils.modules.utils import extracted_data_from_ref


def test_receipts_custom_validation(
    acq_order_fiction_martigny,
    acq_account_fiction_martigny,
    acq_receipt_fiction_martigny,
    acq_receipt_fiction_martigny_data,
):
    """test receipts custom validations."""
    acre1 = acq_receipt_fiction_martigny
    # TEST ADJUSTMENT AMOUNT WITH BAD DECIMALS --------------------------------
    acre1["amount_adjustments"][0]["amount"] = 1.000003
    with pytest.raises(ValidationError) as err:
        acre1 = acre1.update(acre1, dbcommit=True, reindex=True)
    assert "must be multiple of 0.01" in str(err)

    acre1["amount_adjustments"][0]["amount"] = -99999.990
    acre1 = acre1.update(acre1, dbcommit=True, reindex=True)
    acre1.update(acq_receipt_fiction_martigny_data, dbcommit=True, reindex=True)


def test_receipts_properties(
    acq_order_fiction_martigny,
    acq_account_fiction_martigny,
    acq_receipt_fiction_martigny,
    acq_receipt_line_1_fiction_martigny,
    acq_receipt_line_2_fiction_martigny,
    lib_martigny,
):
    """Test receipt properties."""
    acre1 = acq_receipt_fiction_martigny
    acrl1 = acq_receipt_line_1_fiction_martigny
    acrl2 = acq_receipt_line_2_fiction_martigny
    # LIBRARY------------------------------------------------------------------
    assert acre1.library_pid == lib_martigny.pid
    # ORGANISATION ------------------------------------------------------------
    assert acre1.organisation_pid == lib_martigny.organisation_pid
    # ORDER -------------------------------------------------------------------
    assert acre1.order_pid == acq_order_fiction_martigny.pid
    # NOTE --------------------------------------------------------------------
    assert acre1.get_note(AcqReceiptNoteType.STAFF)
    # EXCHANGE_RATE -----------------------------------------------------------
    assert acre1.exchange_rate
    # AMOUNT ------------------------------------------------------------------
    adj_amount = sum(adj.get("amount") for adj in acre1.amount_adjustments)
    wished_amount = sum([acrl1.total_amount, acrl2.total_amount, adj_amount])
    assert acre1.total_amount == wished_amount
    # QUANTITY ----------------------------------------------------------------
    assert acre1.total_item_quantity == sum([acrl1.quantity, acrl2.quantity])
    # ACQ ACCOUNT -------------------------------------------------------------
    for amount in acre1.amount_adjustments:
        assert (
            extracted_data_from_ref(amount.get("acq_account"))
            == acq_account_fiction_martigny.pid
        )
    # RECEIPT LINES -----------------------------------------------------------
    lines = [acrl1, acrl2]
    assert all(line in lines for line in acre1.get_receipt_lines())

    lines_pid = [line.pid for line in lines]
    assert all(pid in lines_pid for pid in acre1.get_receipt_lines("pids"))

    assert acre1.get_receipt_lines("count") == 2
