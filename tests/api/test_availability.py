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

"""Tests availability."""

from unittest import mock

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.documents.api import Document
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.loans.models import LoanAction
from tests.utils import get_json, postdata


def test_item_holding_document_availability(
    client,
    document,
    lib_martigny,
    holding_lib_martigny,
    item_lib_martigny,
    item2_lib_martigny,
    librarian_martigny,
    librarian_saxon,
    patron_martigny,
    patron2_martigny,
    loc_public_saxon,
    circulation_policies,
    ebook_1_data,
    item_lib_martigny_data,
):
    """Test item, holding and document availability."""
    assert item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny.user
    )
    assert item_lib_martigny.is_available()
    assert holding_lib_martigny.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == "standard"
    assert Document.is_available(document.pid, view_code="global")
    assert document_availability_status(client, document.pid, librarian_martigny.user)

    # login as patron
    with mock.patch("rero_ils.modules.patrons.api.current_patrons", [patron_martigny]):
        login_user_via_session(client, patron_martigny.user)
        assert holding_lib_martigny.get_holding_loan_conditions() == "short 15 days"

    # request
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        "api_item.librarian_request",
        {
            "item_pid": item_lib_martigny.pid,
            "patron_pid": patron_martigny.pid,
            "pickup_location_pid": loc_public_saxon.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    actions = data.get("action_applied")
    loan_pid = actions[LoanAction.REQUEST].get("pid")
    assert not item_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny.user
    )
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == "standard"
    assert Document.is_available(document.pid, "global")
    assert document_availability_status(client, document.pid, librarian_martigny.user)

    # validate request
    res, _ = postdata(
        client,
        "api_item.validate_request",
        {
            "item_pid": item_lib_martigny.pid,
            "pid": loan_pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    assert not item_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny.user
    )
    assert not item_lib_martigny.is_available()
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == "standard"
    assert Document.is_available(document.pid, "global")
    assert document_availability_status(client, document.pid, librarian_martigny.user)
    login_user_via_session(client, librarian_saxon.user)
    # receive
    res, _ = postdata(
        client,
        "api_item.receive",
        {
            "item_pid": item_lib_martigny.pid,
            "pid": loan_pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    assert not item_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_saxon.user
    )
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.is_available()
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == "standard"
    assert Document.is_available(document.pid, "global")
    assert document_availability_status(client, document.pid, librarian_martigny.user)
    # checkout
    res, _ = postdata(
        client,
        "api_item.checkout",
        {
            "item_pid": item_lib_martigny.pid,
            "patron_pid": patron_martigny.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.is_available()
    assert not item_availablity_status(client, item.pid, librarian_martigny.user)
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == "standard"
    assert Document.is_available(document.pid, "global")
    assert document_availability_status(client, document.pid, librarian_martigny.user)

    # masked item isn't.is_available()
    item["_masked"] = True
    item = item.update(item, dbcommit=True, reindex=True)
    assert not item.is_available()
    del item["_masked"]
    item.update(item, dbcommit=True, reindex=True)

    # test can not request item already checked out to patron
    res = client.get(
        url_for(
            "api_item.can_request",
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny.get("patron", {}).get("barcode")[0],
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get("can_request")

    end_date = item.get_item_end_date(time_format=None, language="en")

    """
    request second item with another patron and test document and holding
    availability
    """

    # login as patron
    with mock.patch("rero_ils.modules.patrons.api.current_patrons", [patron_martigny]):
        login_user_via_session(client, patron2_martigny.user)
        assert holding_lib_martigny.get_holding_loan_conditions() == "short 15 days"
    # request second item
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        "api_item.librarian_request",
        {
            "item_pid": item2_lib_martigny.pid,
            "patron_pid": patron2_martigny.pid,
            "pickup_location_pid": loc_public_saxon.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    assert not item2_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item2_lib_martigny.pid, librarian_martigny.user
    )
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert not holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == "standard"
    assert not Document.is_available(document.pid, "global")
    assert not document_availability_status(
        client, document.pid, librarian_martigny.user
    )


def item_availablity_status(client, pid, user):
    """Returns item availability."""
    res = client.get(
        url_for(
            "api_item.item_availability",
            pid=pid,
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get("available")


def document_availability_status(client, pid, user):
    """Returns document availability."""
    res = client.get(
        url_for("api_documents.document_availability", pid=pid, view_code="global")
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get("available")


def test_availability_cipo_allow_request(
    client,
    librarian_martigny,
    item_lib_martigny,
    item_type_standard_martigny,
    patron_martigny,
    circ_policy_short_martigny,
):
    """Test availability is cipo disallow request."""
    login_user_via_session(client, librarian_martigny.user)

    # update the cipo to disallow request
    cipo = circ_policy_short_martigny
    cipo["allow_requests"] = False
    cipo.update(cipo.dumps(), dbcommit=True, reindex=True)

    res = client.get(
        url_for(
            "api_item.can_request",
            item_pid=item_lib_martigny.pid,
            patron_barcode=patron_martigny.get("patron", {}).get("barcode")[0],
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get("can")

    # reset the cipo
    cipo["allow_requests"] = True
    cipo.update(cipo.dumps(), dbcommit=True, reindex=True)


def test_document_availability_failed(
    client, item_lib_martigny, document_with_issn, org_martigny
):
    """Test document availability with dummy data should failed."""
    res = client.get(url_for("api_documents.document_availability", pid="dummy_pid"))
    assert res.status_code == 404
    res = client.get(
        url_for("api_documents.document_availability", pid=document_with_issn.pid)
    )
    assert res.status_code == 200
    assert not res.json.get("available")
    res = client.get(
        url_for(
            "api_documents.document_availability",
            pid=document_with_issn.pid,
            view_code=org_martigny["code"],
        )
    )
    assert res.status_code == 200
    assert not res.json.get("available")


def test_item_availability_failed(client, librarian2_martigny):
    """Test item availability with dummy data should failed."""
    res = client.get(url_for("api_item.item_availability", pid="dummy_pid"))
    assert res.status_code == 404


def test_item_availability_extra(client, item_lib_sion):
    """Test item availability with an extra parameters."""
    res = client.get(url_for("api_item.item_availability", pid=item_lib_sion.pid))
    assert list(res.json.keys()) == ["available"]

    res = client.get(
        url_for("api_item.item_availability", pid=item_lib_sion.pid, more_info=1)
    )
    assert list(res.json.keys()) == [
        "available",
        "circulation_message",
        "number_of_request",
        "status",
    ]


def test_holding_availability(client, holding_lib_martigny):
    """Test holding availability endpoint."""
    res = client.get(url_for("api_holding.holding_availability", pid="dummy_pid"))
    assert res.status_code == 404

    res = client.get(
        url_for("api_holding.holding_availability", pid=holding_lib_martigny.pid)
    )
    assert res.status_code == 200
    assert "available" in res.json
