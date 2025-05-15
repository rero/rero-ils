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

"""Tests circulation scenario D."""


from invenio_accounts.testutils import login_user_via_session

from tests.utils import get_json, postdata


def test_circ_scenario_d(
    client,
    librarian_martigny,
    lib_martigny,
    lib_saxon,
    patron_martigny,
    loc_public_martigny,
    item_lib_martigny,
    circulation_policies,
    loc_public_saxon,
    librarian_saxon,
    patron2_martigny,
    lib_fully,
    loc_public_fully,
    librarian_fully,
):
    """Test the fourth circulation scenario."""
    # https://github.com/rero/rero-ils/blob/dev/doc/circulation/scenarios.md
    # An inexperienced librarian A (library A) makes a checkin on item A,
    # which is on shelf at library A and without requests (-> nothing happens).
    # Item A is requested by patron A. Another librarian B of library B tries
    # to check it out for patron B (-> denied). The item is requested by
    # patron B with pickup library B. Librarian B tries again to check it out
    # for patron B (-> denied), then for patron A (-> ok). Patron A tries to
    # renew item A (-> denied). Patron A returns item A at library B. The item
    # is at desk for patron B.

    # Patron A requests it again, with pickup library A. Unexpectedly,
    # libarian A tries to check out item A for patron A (-> denied).
    # He then checks it out for patron B. Patron B returns item A at library C.
    # It goes in transit to library A for patron A.

    # Before arriving to library A, it transits through library B. Patron A
    # cancels his request. Item A transits through library C. It is then
    # received at its owning library A.

    # An inexperienced librarian A (library A) makes a checkin on item A,
    # which is on shelf at library A and without requests (-> nothing happens).
    login_user_via_session(client, librarian_martigny.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 400

    # Item A is requested by patron A.
    circ_params["patron_pid"] = patron_martigny.pid
    res, data = postdata(client, "api_item.librarian_request", dict(circ_params))
    assert res.status_code == 200
    martigny_loan_pid = get_json(res)["action_applied"]["request"]["pid"]

    # Another librarian B of library B tries
    # to check it out for patron B (-> denied).
    login_user_via_session(client, librarian_saxon.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_saxon.pid,
        "transaction_library_pid": lib_saxon.pid,
        "transaction_user_pid": librarian_saxon.pid,
    }
    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 403

    # The item is requested by
    # patron B with pickup library B.
    res, data = postdata(client, "api_item.librarian_request", dict(circ_params))
    assert res.status_code == 200
    saxon_loan_pid = get_json(res)["action_applied"]["request"]["pid"]

    # Librarian B tries again to check it out
    # for patron B (-> denied),
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_saxon.pid,
        "transaction_library_pid": lib_saxon.pid,
        "transaction_user_pid": librarian_saxon.pid,
    }
    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 403
    # then for patron A (-> ok).
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_saxon.pid,
        "transaction_library_pid": lib_saxon.pid,
        "transaction_user_pid": librarian_saxon.pid,
    }

    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 200

    # Patron A tries to renew item A (-> denied).
    res, data = postdata(client, "api_item.extend_loan", dict(circ_params))
    assert res.status_code == 400

    # Patron A returns item A at library B. The item is at desk for patron B.
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200

    # Patron A requests it again, with pickup library A.
    login_user_via_session(client, librarian_martigny.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.librarian_request", dict(circ_params))
    assert res.status_code == 200
    martigny_loan_pid = get_json(res)["action_applied"]["request"]["pid"]

    # Unexpectedly, libarian A tries to check out item A for patron A
    # (-> denied).
    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 403

    # He then checks it out for patron B.
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 200

    # Patron B returns item A at library C.
    # It goes in transit to library A for patron A.
    login_user_via_session(client, librarian_fully.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
        "transaction_library_pid": lib_fully.pid,
        "transaction_user_pid": librarian_fully.pid,
    }
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200

    # Before arriving to library A, it transits through library B.
    login_user_via_session(client, librarian_saxon.user)
    # Patron A
    # cancels his request. Item A transits through library C. It is then
    # received at its owning library A.
    circ_params = {
        "pid": martigny_loan_pid,
        "transaction_library_pid": lib_saxon.pid,
        "transaction_user_pid": librarian_saxon.pid,
    }
    res, data = postdata(client, "api_item.cancel_item_request", dict(circ_params))
    assert res.status_code == 200

    login_user_via_session(client, librarian_martigny.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200
