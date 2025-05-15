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

"""Tests invenio circulation bug when document has items attached."""


from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.loans.models import LoanAction
from tests.utils import postdata


def test_document_with_one_item_attached_bug(
    client,
    librarian_martigny,
    patron_martigny,
    patron2_martigny,
    loc_public_martigny,
    item_type_standard_martigny,
    item_lib_martigny,
    json_header,
    circulation_policies,
    lib_martigny,
):
    """Test document with one item."""
    login_user_via_session(client, librarian_martigny.user)

    # checkout first item1 to patron
    res, data = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    actions = data.get("action_applied")
    loan_pid = actions[LoanAction.CHECKOUT].get("pid")

    # request first item by patron2
    res, data = postdata(
        client,
        "api_item.librarian_request",
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    actions = data.get("action_applied")
    loan2_pid = actions[LoanAction.REQUEST].get("pid")

    # checkin the first item
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    assert item_lib_martigny.number_of_requests() == 1
    res, data = postdata(
        client,
        "api_item.cancel_item_request",
        dict(
            pid=loan2_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    assert item_lib_martigny.number_of_requests() == 0


def test_document_with_items_attached_bug(
    client,
    librarian_martigny,
    patron_martigny,
    patron2_martigny,
    item2_lib_martigny,
    loc_public_martigny,
    item_type_standard_martigny,
    item_lib_martigny,
    json_header,
    circulation_policies,
    lib_martigny,
):
    """Test document with multiple items."""
    login_user_via_session(client, librarian_martigny.user)

    # checkout first item1 to patron
    res, data = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    actions = data.get("action_applied")
    loan_pid = actions[LoanAction.CHECKOUT].get("pid")

    # checkout second item2 to patron
    res, data = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    actions = data.get("action_applied")
    loan2_pid = actions[LoanAction.CHECKOUT].get("pid")

    # request first item by patron2
    res, data = postdata(
        client,
        "api_item.librarian_request",
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    # request second item by patron2
    res, data = postdata(
        client,
        "api_item.librarian_request",
        dict(
            item_pid=item2_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    assert item_lib_martigny.number_of_requests() == 1
    assert item2_lib_martigny.number_of_requests() == 1

    # checkin the first item
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    assert item_lib_martigny.number_of_requests() == 1
    assert item2_lib_martigny.number_of_requests() == 1

    # checkin the second item
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan2_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    assert item_lib_martigny.number_of_requests() == 1
    assert item2_lib_martigny.number_of_requests() == 1
