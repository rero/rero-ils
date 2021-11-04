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

from rero_ils.modules.acq_receipts.models import AcqReceiptNoteType
from rero_ils.modules.utils import extracted_data_from_ref


def test_receipts_properties(acq_order_fiction_martigny,
                             acq_account_fiction_martigny,
                             acq_receipt_fiction_martigny, lib_martigny):
    """Test receipt properties."""
    acre1 = acq_receipt_fiction_martigny
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
    amounts = acre1.amount_adjustments
    assert amounts
    assert acre1.total_amount == \
        sum([fee.get('amount') for fee in amounts])
    # ACQ ACCOUNT -------------------------------------------------------------
    for amount in amounts:
        assert extracted_data_from_ref(amount.get('acq_account')) == \
            acq_account_fiction_martigny.pid
