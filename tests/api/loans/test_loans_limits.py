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

"""Loan Record limits."""
from copy import deepcopy

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import LoanAction
from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.utils import get_ref_for_pid


def test_loans_limits_checkout_library_limits(
     client, app, librarian_martigny_no_email, lib_martigny,
     patron_type_children_martigny, item_lib_martigny, item2_lib_martigny,
     item3_lib_martigny, item_lib_martigny_data, item2_lib_martigny_data,
     item3_lib_martigny_data, loc_public_martigny, patron_martigny_no_email,
     circ_policy_short_martigny):
    """Test checkout library limits."""

    patron = patron_martigny_no_email
    item2_original_data = deepcopy(item2_lib_martigny_data)
    item3_original_data = deepcopy(item3_lib_martigny_data)
    item1 = item_lib_martigny
    item2 = item2_lib_martigny
    item3 = item3_lib_martigny
    library_ref = get_ref_for_pid('lib', lib_martigny.pid)
    location_ref = get_ref_for_pid('loc', loc_public_martigny.pid)

    login_user_via_session(client, librarian_martigny_no_email.user)

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
        transaction_user_pid=librarian_martigny_no_email.pid,
    ))
    assert res.status_code == 200
    loan1_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')

    # Second checkout
    #   --> The library limit exception should be raised.
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item2.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
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
        transaction_user_pid=librarian_martigny_no_email.pid,
    ))
    assert res.status_code == 200
    loan2_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item3.pid,
        patron_pid=patron.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
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
        transaction_user_pid=librarian_martigny_no_email.pid,
    ))
    assert res.status_code == 403
    assert 'Checkout denied' in data['message']

    # reset fixtures
    #   --> checkin both loaned item
    #   --> reset patron_type to original value
    #   --> reset items to original values
    res, data = postdata(client, 'api_item.checkin', dict(
        item_pid=item2.pid,
        pid=loan2_pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
    ))
    assert res.status_code == 200
    res, data = postdata(client, 'api_item.checkin', dict(
        item_pid=item1.pid,
        pid=loan1_pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
    ))
    assert res.status_code == 200
    del patron_type['limits']
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    item2.update(item2_original_data, dbcommit=True, reindex=True)
    item3.update(item3_original_data, dbcommit=True, reindex=True)
