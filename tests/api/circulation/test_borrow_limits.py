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

"""Borrow limits."""
from copy import deepcopy
from datetime import datetime, timedelta

from flask import url_for
from freezegun import freeze_time
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.loans.api import Loan, get_overdue_loans
from rero_ils.modules.loans.models import LoanAction
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.notifications.dispatcher import Dispatcher
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.utils import get_notification
from rero_ils.modules.patron_transaction_events.api import \
    PatronTransactionEvent
from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import get_ref_for_pid


def test_checkout_library_limit(
     client, app, librarian_martigny, lib_martigny,
     patron_type_children_martigny, item_lib_martigny, item2_lib_martigny,
     item3_lib_martigny, item_lib_martigny_data, item2_lib_martigny_data,
     item3_lib_martigny_data, loc_public_martigny, patron_martigny,
     circ_policy_short_martigny):
    """Test checkout library limits."""

    patron = patron_martigny
    item2_original_data = deepcopy(item2_lib_martigny_data)
    item3_original_data = deepcopy(item3_lib_martigny_data)
    item1 = item_lib_martigny
    item2 = item2_lib_martigny
    item3 = item3_lib_martigny
    library_ref = get_ref_for_pid('lib', lib_martigny.pid)
    location_ref = get_ref_for_pid('loc', loc_public_martigny.pid)

    login_user_via_session(client, librarian_martigny.user)

    # Update fixtures for the tests
    #   * Update the patron_type to set a checkout limits
    #   * All items are linked to the same library/location
    patron_type = patron_type_children_martigny
    patron_type['limits'] = {
        'checkout_limits': {
            'global_limit': 3,
            'library_limit': 2,
            'library_exceptions': [{
                'library': {'$ref': library_ref},
                'value': 1
            }]
        }
    }
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    patron_type = PatronType.get_record_by_pid(patron_type.pid)
    item2_lib_martigny_data['location']['$ref'] = location_ref
    item2.update(item2_lib_martigny_data, dbcommit=True, reindex=True)
    item3_lib_martigny_data['location']['$ref'] = location_ref
    item3.update(item3_lib_martigny_data, dbcommit=True, reindex=True)

    # First checkout - All should be fine.
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item1.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 200
    loan1_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')

    # Second checkout
    #   --> The library limit exception should be raised.
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item2.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 403
    assert 'Checkout denied' in data['message']

    # remove the library specific exception and try a new checkout
    #   --> As the limit by library is now '2', the checkout will be done.
    #   --> Try a third checkout : the default library_limit exception should
    #       be raised
    patron_type['limits'] = {
        'checkout_limits': {
            'global_limit': 3,
            'library_limit': 2,
        }
    }
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item2.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 200
    loan2_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item3.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 403
    assert 'Checkout denied' in data['message']

    # remove the library default limit and update the global_limit to 2.
    #   --> try the third checkout : the global_limit exception should now be
    #       raised
    patron_type['limits'] = {
        'checkout_limits': {
            'global_limit': 2
        }
    }
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item3.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 403
    assert 'Checkout denied' in data['message']

    # check the circulation information API
    url = url_for(
        'api_patrons.patron_circulation_informations',
        patron_pid=patron.pid
    )
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert 'error' == data['messages'][0]['type']
    assert 'Checkout denied' in data['messages'][0]['content']

    # try a checkout with 'override_blocking' parameter.
    #   --> the restriction is no longer checked, the checkout will be success.
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item3.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ), url_data={'override_blocking': 'true'})
    assert res.status_code == 200
    loan3_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')

    # reset fixtures
    #   --> checkin three loaned item
    #   --> reset patron_type to original value
    #   --> reset items to original values
    res, data = postdata(client, 'api_item.checkin', dict(
        item_pid=item3.pid,
        pid=loan3_pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    res, data = postdata(client, 'api_item.checkin', dict(
        item_pid=item2.pid,
        pid=loan2_pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 200
    res, data = postdata(client, 'api_item.checkin', dict(
        item_pid=item1.pid,
        pid=loan1_pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 200
    del patron_type['limits']
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    item2.update(item2_original_data, dbcommit=True, reindex=True)
    item3.update(item3_original_data, dbcommit=True, reindex=True)


@freeze_time("2021-06-15")
def test_overdue_limit(
     client, app, librarian_martigny, lib_martigny, item_lib_martigny,
     item2_lib_martigny, patron_type_children_martigny,
     item3_lib_martigny, item_lib_martigny_data, item2_lib_martigny_data,
     item3_lib_martigny_data, loc_public_martigny, patron_martigny,
     circ_policy_short_martigny, lib_saxon, loc_public_saxon):
    """Test overdue limit."""

    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny.pid
    date_format = '%Y/%m/%dT%H:%M:%S.000Z'
    today = datetime.utcnow()
    eod = today.replace(hour=23, minute=59, second=0, microsecond=0,
                        tzinfo=lib_martigny.get_timezone())

    # STEP 0 :: Prepare data for test
    #   * Update the patron_type to set a overdue_items_limit rule.
    #     We define than only 1 overdue items are allowed. Trying a second
    #     checkout is disallowed if patron has an overdue item
    patron_type = patron_type_children_martigny
    patron_type \
        .setdefault('limits', {}) \
        .setdefault('overdue_items_limits', {}) \
        .setdefault('default_value', 1)
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    patron_type = PatronType.get_record_by_pid(patron_type.pid)
    assert patron_type\
        .get('limits', {})\
        .get('overdue_items_limits', {}) \
        .get('default_value') == 1

    # STEP 1 :: Create an checkout with a end_date at the current date
    #   * Create a checkout and set end_date to a fixed_date equals to
    #     current tested date. The loan should not be considered as overdue
    #     and a second checkout should be possible
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
            end_date=eod.strftime(date_format)
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    assert not loan.is_loan_overdue()

    tmp_item_data = deepcopy(item_lib_martigny_data)
    del tmp_item_data['pid']
    del tmp_item_data['barcode']
    tmp_item_data['library']['$ref'] = get_ref_for_pid('lib', lib_saxon.pid)
    tmp_item_data['location']['$ref'] = \
        get_ref_for_pid('loc', loc_public_saxon.pid)
    tmp_item = Item.create(tmp_item_data, dbcommit=True, reindex=True)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=tmp_item.pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=tmp_item.pid,
            pid=data.get('action_applied')[LoanAction.CHECKOUT].get('pid'),
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200

    # STEP 2 :: Set the loan as overdue and test a new checkout
    #   Now there is one loan in overdue, then the limit is reached and a new
    #   checkout shouldn't be possible
    end_date = eod - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    overdue_loans = list(get_overdue_loans(patron_pid=patron_pid))
    assert loan.is_loan_overdue()
    assert loan.end_date == end_date.isoformat()
    assert overdue_loans[0].get('pid') == loan_pid
    assert not get_notification(loan, NotificationType.OVERDUE)

    notification = loan.create_notification(
        _type=NotificationType.OVERDUE).pop()
    Dispatcher.dispatch_notifications([notification.get('pid')])
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    assert get_notification(loan, NotificationType.OVERDUE)

    # Try a second checkout - limit should be reached
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 403
    assert 'Checkout denied' in data['message']
    # Try a request - limit should be reached
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 403
    assert 'maximal number of overdue items is reached' in data['message']
    # Try to extend - limit should be reached
    res, _ = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 403
    assert 'maximal number of overdue items is reached' in data['message']

    # reset the patron_type with default value
    del patron_type['limits']

    # [2] test fee amount limit

    # Update the patron_type to set a fee_amount_limit rule
    patron_type \
        .setdefault('limits', {}) \
        .setdefault('fee_amount_limits', {}) \
        .setdefault('default_value', 0.5)
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    patron_type = PatronType.get_record_by_pid(patron_type.pid)
    assert patron_type.get('limits', {}).get('fee_amount_limits', {}) \
        .get('default_value') == 0.5

    # [2.1] test fee amount limit when we try to checkout a second item
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 403
    assert 'maximal overdue fee amount is reached' in data['message']

    # [2.2] test fee amount limit when we try to request another item
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 403
    assert 'maximal overdue fee amount is reached' in data['message']

    # [2.3] test fee amount limit when we try to extend loan
    res, _ = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )

    assert res.status_code == 403
    assert 'maximal overdue fee amount is reached' in data['message']

    # reset the patron_type with default value
    del patron_type['limits']
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    patron_type = PatronType.get_record_by_pid(patron_type.pid)
    assert patron_type.get('limits') is None

    # # checkin the item to put it back to it's original state
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200


def test_unpaid_subscription(
    client, app, librarian_martigny, lib_martigny, item_lib_martigny,
    patron_type_children_martigny, patron_type_children_martigny_data,
    loc_public_martigny, patron_martigny, circ_policy_short_martigny
):
    """Test unpaid subscription restriction limit."""
    item = item_lib_martigny
    patron = patron_martigny
    patron_type = patron_type_children_martigny

    login_user_via_session(client, librarian_martigny.user)

    # STEP#0 :: Prepare data for test
    #   * Update the patron_type to set a unpaid_subscription limit rule to
    #     False => Even if patron has unpaid subscription, any circulation
    #     operation should be possible.
    patron_type \
        .setdefault('limits', {}) \
        .setdefault('unpaid_subscription', True)
    patron_type.setdefault('subscription_amount', 10)
    patron_type = patron_type.update(patron_type, dbcommit=True, reindex=True)

    # STEP#1 :: Create an unpaid subscription for patron
    assert not patron.pending_subscriptions
    subscription_start = datetime.now()
    subscription_end = subscription_start + timedelta(days=365)
    patron.add_subscription(patron_type, subscription_start, subscription_end)
    subscriptions = patron.pending_subscriptions
    assert len(subscriptions) == 1
    subscription = subscriptions[0]

    # STEP#2 :: Try a circulation operation
    #   As patron doesn't yet paid the subscription and we set a limit at
    #   STEP#0, any checkout operation should be denied.
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 403
    assert 'Checkout denied' in data['message'] and 'unpaid' in data['message']
    # STEP#3 :: Pay the subscription and retry a circulation operation
    #   As the subscription will be paid the checkout operation must be granted
    data = {
        'parent': subscription['patron_transaction'],
        'creation_date': datetime.now().isoformat(),
        'type': 'payment',
        'subtype': 'cash',
        'amount': patron_type['subscription_amount'],
        'operator': {'$ref': get_ref_for_pid(Patron, librarian_martigny.pid)}
    }
    PatronTransactionEvent.create(data, dbcommit=True, reindex=True)
    assert not patron.pending_subscriptions

    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 200
    loan_pid = data['action_applied']['checkout']['pid']

    # RESET DATA
    #   * check-in the item
    #   * reset the patron_type
    res, _ = postdata(client, 'api_item.checkin', dict(
        item_pid=item.pid,
        pid=loan_pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res == 200
    patron_type.update(patron_type_children_martigny_data,
                       dbcommit=True, reindex=True)
