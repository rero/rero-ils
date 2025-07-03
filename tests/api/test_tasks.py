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

"""Tasks tests."""

from datetime import datetime, timedelta, timezone

import ciso8601
from freezegun import freeze_time
from invenio_accounts.testutils import login_user_via_session
from invenio_records.signals import after_record_update

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.tasks import (
    clean_obsolete_temporary_item_types_and_locations,
)
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import (
    Loan,
    LoansSearch,
    get_due_soon_loans,
    get_overdue_loans,
)
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.loans.tasks import cancel_expired_request_task
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.tasks import create_notifications
from rero_ils.modules.notifications.utils import (
    get_notification,
    number_of_notifications_sent,
)
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.listener import create_subscription_patron_transaction
from rero_ils.modules.patrons.tasks import (
    check_patron_types_and_add_subscriptions as check_patron_types_and_add_subscriptions,
)
from rero_ils.modules.patrons.tasks import (
    clean_obsolete_subscriptions,
    task_clear_and_renew_subscriptions,
)
from rero_ils.modules.utils import add_years, get_ref_for_pid
from tests.utils import postdata


def test_notifications_task(
    client,
    librarian_martigny,
    patron_martigny,
    item_lib_martigny,
    circ_policy_short_martigny,
    loc_public_martigny,
    lib_martigny,
):
    """Test overdue and due_soon loans."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny.pid
    # First we need to create a checkout
    res, data = postdata(
        client,
        "api_item.checkout",
        {
            "item_pid": item_pid,
            "patron_pid": patron_pid,
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    loan_pid = data.get("action_applied")[LoanAction.CHECKOUT].get("pid")
    loan = Loan.get_record_by_pid(loan_pid)

    # test due_soon notification
    #   update the loan end_date to reflect the due_soon date. So when we run
    #   the task to create notification this loan should be considered as
    #   due_soon and a notification should be created.
    end_date = datetime.now(timezone.utc) + timedelta(days=5)
    loan["end_date"] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    LoansSearch.flush_and_refresh()
    due_soon_loans = list(get_due_soon_loans())
    assert due_soon_loans[0].get("pid") == loan_pid

    create_notifications(types=[NotificationType.DUE_SOON, NotificationType.OVERDUE])
    NotificationsSearch.flush_and_refresh()
    LoansSearch.flush_and_refresh()
    assert loan.is_notified(NotificationType.DUE_SOON)

    notif = get_notification(loan, NotificationType.DUE_SOON)
    notif_date = ciso8601.parse_datetime(notif.get("creation_date"))
    assert notif_date.date() == datetime.today().date()

    # -- test overdue notification --

    # For this test, we simulate an overdue on Friday and the library is closed
    # during the weekend. No notification should be generated.

    # Friday
    end_date = datetime(year=2021, month=1, day=22, tzinfo=timezone.utc)
    loan["end_date"] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    # Process the notification during the weekend (Saturday)
    process_date = datetime(year=2021, month=1, day=23, tzinfo=timezone.utc)
    overdue_loans = list(get_overdue_loans(tstamp=process_date))
    assert overdue_loans[0].get("pid") == loan_pid
    create_notifications(types=[NotificationType.OVERDUE], tstamp=process_date)
    NotificationsSearch.flush_and_refresh()
    LoansSearch.flush_and_refresh()
    # Should not be created
    assert not loan.is_notified(NotificationType.OVERDUE, 1)
    # Should not be sent
    assert (
        number_of_notifications_sent(loan, notification_type=NotificationType.OVERDUE)
        == 0
    )

    #   For this test, we will update the loan to simulate an overdue of 12
    #   days. With this delay, regarding the cipo configuration, only the first
    #   overdue reminder should be sent.
    #   NOTE : the cipo define the first overdue reminder after 5 days. But we
    #          use an overdue of 12 days because the overdue is based on
    #          loan->item->library open days. Using 12 (5 days + 1 week) we
    #          ensure than the overdue notification will be sent.
    loan_lib = Library.get_record_by_pid(loan.library_pid)
    add_days = 12
    open_days = []
    while len(open_days) < 12:
        end_date = datetime.now(timezone.utc) - timedelta(days=add_days)
        open_days = loan_lib.get_open_days(end_date)
        add_days += 1

    loan["end_date"] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    overdue_loans = list(get_overdue_loans())
    assert overdue_loans[0].get("pid") == loan_pid

    create_notifications(types=[NotificationType.DUE_SOON, NotificationType.OVERDUE])
    NotificationsSearch.flush_and_refresh()
    LoansSearch.flush_and_refresh()
    assert loan.is_notified(NotificationType.OVERDUE, 0)
    assert (
        number_of_notifications_sent(loan, notification_type=NotificationType.OVERDUE)
        == 1
    )

    # test overdue notification#2
    #   Now simulate than the previous call crashed. So call the task with a
    #   fixed date. In our test, no new notifications should be sent
    create_notifications(
        types=[NotificationType.DUE_SOON, NotificationType.OVERDUE],
        tstamp=datetime.now(timezone.utc),
    )
    assert (
        number_of_notifications_sent(loan, notification_type=NotificationType.OVERDUE)
        == 1
    )

    # test overdue notification#3
    #   For this test, we will update the loan to simulate an overdue of 40
    #   days. With this delay, regarding the cipo configuration, the second
    #   (and last) overdue reminder should be sent.
    end_date = datetime.now(timezone.utc) - timedelta(days=40)
    loan["end_date"] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    overdue_loans = list(get_overdue_loans())
    assert overdue_loans[0].get("pid") == loan_pid

    create_notifications(types=[NotificationType.DUE_SOON, NotificationType.OVERDUE])
    NotificationsSearch.flush_and_refresh()
    LoansSearch.flush_and_refresh()
    assert loan.is_notified(NotificationType.OVERDUE, 1)
    assert (
        number_of_notifications_sent(loan, notification_type=NotificationType.OVERDUE)
        == 2
    )

    # checkin the item to put it back to it's original state
    res, _ = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item_pid,
            "pid": loan_pid,
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200


def test_clear_and_renew_subscription(patron_type_grown_sion, patron_sion):
    """Test the `task patrons.tasks.clear_and_renew_subscription`."""
    patron_sion = patron_sion

    # To test correctly all the code we need to disconnect the listener
    # `create_subscription_patron_transaction` method. Otherwise, the
    # first part of the task (clean_obsolete_subscriptions) will automatically
    # create new subscriptions because the last instruction is a
    # `patron.update()` call.
    after_record_update.disconnect(create_subscription_patron_transaction)

    # first step : clear all subscription for the patron and crate an new
    # obsolete subscription.
    if "subscriptions" in patron_sion.get("patron", {}):
        del patron_sion["patron"]["subscriptions"]
    start = datetime.now() - timedelta(days=200)
    end = start + timedelta(days=100)
    patron_sion.add_subscription(patron_type_grown_sion, start, end)
    assert len(patron_sion.get("patron", {}).get("subscriptions", [])) == 1
    assert patron_sion.get("patron", {})["subscriptions"][0][
        "end_date"
    ] == end.strftime("%Y-%m-%d")

    # clean old subscription - Reload the patron and check they are no more
    # subscriptions
    clean_obsolete_subscriptions()
    patron_sion = Patron.get_record_by_pid(patron_sion.pid)
    assert len(patron_sion.get("patron", {}).get("subscriptions", [])) == 0

    # check for patron needed subscriptions and create new subscription if
    # needed. As our patron has no subscription and is still connected to
    # a patron type requiring subscription, this task should create a
    # new subscription for this patron
    check_patron_types_and_add_subscriptions()
    patron_sion = Patron.get_record_by_pid(patron_sion.pid)
    assert len(patron_sion.get("patron", {}).get("subscriptions", [])) == 1
    assert patron_sion.get("patron", {})["subscriptions"][0]["end_date"] == add_years(
        datetime.now(), 1
    ).strftime("%Y-%m-%d")

    # run both operation using task_clear_and_renew_subscriptions` and check
    # the result. The patron should still have one subscription but end_date
    # must be today.
    del patron_sion["patron"]["subscriptions"]
    start = datetime.now() - timedelta(days=200)
    end = start + timedelta(days=100)
    patron_sion.add_subscription(patron_type_grown_sion, start, end)
    task_clear_and_renew_subscriptions()
    patron_sion = Patron.get_record_by_pid(patron_sion.pid)
    assert len(patron_sion.get("patron", {}).get("subscriptions", [])) == 1
    assert patron_sion.get("patron", {})["subscriptions"][0][
        "end_date"
    ] != end.strftime("%Y-%m-%d")

    # as we disconnect the `create_subscription_patron_transaction` listener
    # at the beginning, we need to connect it now.
    after_record_update.connect(create_subscription_patron_transaction)


def test_clear_obsolete_temporary_item_type_and_location(
    item_lib_martigny,
    item_type_on_site_martigny,
    loc_restricted_martigny,
    item2_lib_martigny,
):
    """Test task test_clear_obsolete_temporary_item_type_and_location"""
    item = item_lib_martigny
    end_date = datetime.now() + timedelta(days=2)
    item["temporary_item_type"] = {
        "$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    item["temporary_location"] = {
        "$ref": get_ref_for_pid("loc", loc_restricted_martigny.pid),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    item = item.update(item, dbcommit=True, reindex=True)
    assert item.get("temporary_item_type", {}).get("end_date")
    assert item.get("temporary_location", {}).get("end_date")

    end_date = datetime.now() + timedelta(days=25)
    item2_lib_martigny["temporary_item_type"] = {
        "$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    item2_lib_martigny["temporary_location"] = {
        "$ref": get_ref_for_pid("loc", loc_restricted_martigny.pid),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }
    item2_lib_martigny = item2_lib_martigny.update(
        item2_lib_martigny, dbcommit=True, reindex=True
    )
    assert item2_lib_martigny.get("temporary_item_type", {}).get("end_date")
    assert item2_lib_martigny.get("temporary_location", {}).get("end_date")

    over_4_days = datetime.now() + timedelta(days=4)
    with freeze_time(over_4_days.strftime("%Y-%m-%d")):
        items = Item.get_items_with_obsolete_temporary_item_type_or_location()
        assert len(list(items))
        # run the tasks
        msg = clean_obsolete_temporary_item_types_and_locations()
        assert msg["deleted fields"] == 2
        # check after task was ran
        items = Item.get_items_with_obsolete_temporary_item_type_or_location()
        assert len(list(items)) == 0
        item = Item.get_record_by_pid(item.pid)
        assert not item.get("temporary_item_type")
        assert not item.get("temporary_location")


def test_expired_request_task(
    item_on_shelf_martigny_patron_and_loan_pending,
    yesterday,
    loc_public_martigny,
    patron2_martigny,
    librarian_martigny,
):
    """Test the task cancelling the expired request."""
    # STEP#0 :: CREATE TWO REQUEST
    #   * Create an initial request and validate it.
    #   * Create a second request for an other patron.
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending
    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    item, _ = item.validate_request(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    item, actions = item.request(
        pickup_location_pid=loc_public_martigny.pid,
        patron_pid=patron2_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    )
    assert "request" in actions
    loan2 = Loan.get_record_by_pid(actions["request"]["pid"])

    # STEP#1 :: SET FIRST REQUEST AS EXPIRED
    #   Update the first request (Loan) to set it as expired updating its
    #   `request_expired_date` attribute.
    loan["request_expire_date"] = yesterday.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    LoansSearch.flush_and_refresh()
    loan = LoansSearch().get_record_by_pid(loan.pid)

    # STEP#2 :: RUN THE TASK
    #   * run the 'cancel_expired_request' task.
    #   * check the first request is now CANCELLED
    #   * check the second request is now ready to pickup (state=ITEM_AT_DESK)
    task_result = cancel_expired_request_task()
    assert task_result == (1, 1)
    loan = Loan.get_record_by_pid(loan.pid)
    loan2 = Loan.get_record_by_pid(loan2.pid)
    assert loan["state"] == LoanState.CANCELLED
    assert loan2["state"] == LoanState.ITEM_AT_DESK
