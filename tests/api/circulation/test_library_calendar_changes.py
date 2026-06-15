# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test library calendar changes effects on related loans."""

import time

from invenio_accounts.testutils import login_user_via_session
from invenio_cache import current_cache

from rero_ils.modules.loans.api import Loan
from tests.utils import postdata


def test_library_calendar_changes(
    client,
    librarian_martigny,
    lib_martigny,
    lib_martigny_data,
    patron_martigny,
    loc_public_martigny,
    item_lib_martigny,
    circulation_policies,
):
    """Test changes on library calendar and loan implication."""

    def get_cache(library_pid):
        cache_content = current_cache.get("library-calendar-changes") or {}
        return cache_content.get(library_pid, {})

    login_user_via_session(client, librarian_martigny.user)
    library = lib_martigny

    # INITIALIZATION :: Create a loan
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": library.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", circ_params)
    assert res.status_code == 200
    loan_pid = res.json["action_applied"]["checkout"]["pid"]
    loan = Loan.get_record_by_pid(loan_pid)

    # TEST#1 :: Changes on an untracked field.
    #   Related loan shouldn't be updated
    initial_enddate = loan.end_date
    library["code"] = "new code"
    library = library.update(library, dbcommit=True, reindex=False)
    loan = Loan.get_record_by_pid(loan_pid)
    assert loan.end_date == initial_enddate

    # TEST#2 :: Changes on library calendar
    #   * Changes an 'open' day to a 'closed' day.
    #   * Add an exception date on the "end date" day of the loan.
    #   * A `calendar_changes_update_loans` task should be run ; wait to the
    #     end of the task to check if the "end date" of the loan has been
    #     updated.
    library["opening_hours"][0] = {"day": "sunday", "is_open": False}
    library["exception_dates"].append({"is_open": False, "title": "exception date", "start_date": loan.end_date[:10]})
    library = library.update(library, dbcommit=True, reindex=False)

    time.sleep(5)  # TODO :: find a better way to detect task is finished.
    loan = Loan.get_record_by_pid(loan_pid)
    assert loan.end_date != initial_enddate

    # RESET FIXTURES
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, _ = postdata(client, "api_item.checkin", circ_params)
    assert res.status_code == 200
    library.update(lib_martigny_data, dbcommit=True, reindex=True)
