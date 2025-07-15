# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Test item circulation extend actions at external library."""

from datetime import datetime, timedelta, timezone

import ciso8601
from freezegun import freeze_time

from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.loans.utils import get_circ_policy, get_extension_params
from rero_ils.modules.utils import get_ref_for_pid
from tests.utils import item_record_to_a_specific_loan_state


def test_item_loans_extend_duration(
    item_lib_martigny,
    librarian_martigny,
    patron_martigny,
    loc_public_martigny,
    circulation_policies,
    lib_martigny,
):
    """Test loan extend duration."""
    # Note: this test moved here from the file test_loans_api.py because of
    # tests fixtures conflicts.
    for now_str in [
        # winter time
        "2021-12-13 06:00:00",
        "2022-12-13 20:00:00",
        # winter to summer time
        "2022-03-07 06:00:00",
        "2022-03-07 20:00:00",
        # summer time
        "2022-06-13 05:00:00",
        "2022-06-13 19:00:00",
        # summer to winter time
        "2022-10-10 05:00:00",
        "2022-10-10 19:00:00",
    ]:
        with freeze_time(now_str, tz_offset=0):
            # do a checkout
            item, actions = item_lib_martigny.checkout(
                patron_pid=patron_martigny.pid,
                transaction_location_pid=loc_public_martigny.pid,
                transaction_user_pid=librarian_martigny.pid,
            )
            loan_pid = actions["checkout"]["pid"]
            # assert loan_pid
            loan = Loan.get_record_by_pid(loan_pid)
            end_date = ciso8601.parse_datetime(loan.get("end_date"))
            policy = get_circ_policy(loan, checkout_location=True)
            # do the extend one day before the end date at 3pm
            extend_action_date = (end_date - timedelta(days=1)).replace(hour=15)
            with freeze_time(extend_action_date.isoformat()):
                duration = get_extension_params(loan, parameter_name="duration_default")
                now = datetime.now(timezone.utc)
                utc_end_date = now + duration
                # computed end date at the library timezone
                end_date = utc_end_date.astimezone(tz=lib_martigny.get_timezone())
                expected_utc_end_date = now + timedelta(days=policy["renewal_duration"])
                # expected end date at the library timezone
                expected_end_date = expected_utc_end_date.astimezone(
                    lib_martigny.get_timezone()
                )
                assert end_date.strftime("%Y-%m-%d") == expected_end_date.strftime(
                    "%Y-%m-%d"
                )
                assert end_date.hour == 23
                assert end_date.minute == 59
            # checkin the item for the next tests
            item_lib_martigny.checkin(
                patron_pid=patron_martigny.pid,
                transaction_location_pid=loc_public_martigny.pid,
                transaction_user_pid=librarian_martigny.pid,
            )


def test_extend_on_item_on_loan_with_no_requests_external_library(
    app,
    item_lib_martigny,
    patron_martigny,
    item_type_on_site_martigny,
    loc_public_martigny,
    librarian_martigny,
    lib_martigny,
    lib_saxon,
    loc_public_saxon,
    patron_type_adults_martigny,
    circulation_policies,
):
    """Test extend an on_loan item at an external library."""
    patron_martigny["patron"]["type"]["$ref"] = get_ref_for_pid(
        "ptty", patron_type_adults_martigny.pid
    )
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)
    item_lib_martigny["item_type"]["$ref"] = get_ref_for_pid(
        "itty", item_type_on_site_martigny.pid
    )
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)
    # the library level cipo3 is used here circ_policy_temp_martigny
    params = {
        "patron_pid": patron_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_ON_LOAN,
        params=params,
        copy_item=True,
    )

    settings = app.config["CIRCULATION_POLICIES"]["extension"]
    app.config["CIRCULATION_POLICIES"]["extension"]["from_end_date"] = True
    loan["end_date"] = loan["start_date"]
    initial_loan = loan.update(loan, dbcommit=True, reindex=True)
    assert get_circ_policy(loan, checkout_location=True) == get_circ_policy(loan)
    # The cipo used for the checkout or renewal is "short" which is configured
    # only for lib_martigny. For other libraries it is the default cipo to be
    # used.
    params = {
        "transaction_location_pid": loc_public_saxon.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    cipo = get_circ_policy(loan)
    item, actions = item.extend_loan(**params)
    loan = Loan.get_record_by_pid(initial_loan.pid)
    # now the extend action does not take into account anymore the transaction
    # library so it continues to use the "short" policy for the extend action.
    assert get_circ_policy(loan, checkout_location=True).get("pid") == cipo.get("pid")
    assert get_circ_policy(loan).get("pid") != cipo.get("pid")
