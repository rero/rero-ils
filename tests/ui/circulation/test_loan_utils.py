# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Tests loan utils methods."""

from copy import deepcopy

import pytest
from invenio_circulation.errors import CirculationException
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.loans.api import (
    Loan,
    get_last_transaction_loc_for_item,
    get_loans_by_patron_pid,
)
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.loans.utils import can_be_requested
from rero_ils.modules.locations.api import LocationsSearch


def test_loan_utils(
    client,
    patron_martigny,
    patron2_martigny,
    circulation_policies,
    item_lib_martigny,
    librarian_martigny,
    loc_public_martigny,
):
    """Test loan utils methods."""
    loan_metadata = dict(item_lib_martigny)
    loan_metadata["item_pid"] = item_pid_to_object(item_lib_martigny.pid)
    if "patron_pid" not in loan_metadata:
        loan_metadata["patron_pid"] = patron_martigny.pid
    # Create "virtual" Loan (not registered)
    loan = Loan(loan_metadata)
    # test that loan can successfully move to the pending state
    assert can_be_requested(loan)

    # test that loan without an item may not move to the pending state
    del loan["item_pid"]
    with pytest.raises(Exception):
        assert can_be_requested(loan)

    # test a pending loan will be attached at the right organisation and
    # will not be considered as an active loan
    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, loan_pending_martigny = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.PENDING,
        params=params,
        copy_item=True,
    )

    assert loan_pending_martigny.patron_pid == patron2_martigny.pid
    assert not loan_pending_martigny.is_active
    assert loan_pending_martigny.organisation_pid

    # test required parameters for get_loans_by_patron_pid
    with pytest.raises(TypeError):
        assert get_loans_by_patron_pid()
    assert get_loans_by_patron_pid(patron2_martigny.pid)

    # test required parameters for get_last_transaction_loc_for_item
    with pytest.raises(TypeError):
        assert get_last_transaction_loc_for_item()

    # test the organisation of the loan is based on the item
    new_loan = deepcopy(loan_pending_martigny)
    assert new_loan.organisation_pid == "org1"
    del new_loan["item_pid"]
    assert new_loan.organisation_pid == "org1"
    assert not can_be_requested(loan_pending_martigny)

    # test the allow request at the location level
    loc_public_martigny["allow_request"] = False
    loc_public_martigny.update(loc_public_martigny, dbcommit=True, reindex=True)
    LocationsSearch.flush_and_refresh()
    new_loan = {
        "patron_pid": patron_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    with pytest.raises(CirculationException):
        item, loan_pending_martigny = item_record_to_a_specific_loan_state(
            item=item_lib_martigny,
            loan_state=LoanState.PENDING,
            params=params,
            copy_item=True,
        )

    loc_public_martigny["allow_request"] = True
    loc_public_martigny.update(loc_public_martigny, dbcommit=True, reindex=True)
    LocationsSearch.flush_and_refresh()
    item, loan_pending_martigny = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.PENDING,
        params=params,
        copy_item=True,
    )
    assert loan_pending_martigny["state"] == LoanState.PENDING
