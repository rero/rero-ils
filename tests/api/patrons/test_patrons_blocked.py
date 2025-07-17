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

"""Tests REST API patrons."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.utils import can_be_requested
from tests.utils import get_json, item_pid_to_object


def test_blocked_field_exists(
    client, librarian_martigny, patron_martigny, patron3_martigny_blocked
):
    """Test ptrn6 have blocked field present and set to False."""
    login_user_via_session(client, librarian_martigny.user)
    patron3 = patron3_martigny_blocked

    # non blocked patron
    non_blocked_patron_url = url_for(
        "invenio_records_rest.ptrn_item", pid_value=patron_martigny.pid
    )
    res = client.get(non_blocked_patron_url)
    assert res.status_code == 200
    data = get_json(res)
    assert "blocked" in data["metadata"]["patron"]
    assert data["metadata"]["patron"]["blocked"] is False

    # blocked patron
    blocked_patron_url = url_for(
        "invenio_records_rest.ptrn_item", pid_value=patron3_martigny_blocked.pid
    )
    res = client.get(blocked_patron_url)
    assert res.status_code == 200
    data = get_json(res)
    assert "blocked" in data["metadata"]["patron"]
    assert data["metadata"]["patron"]["blocked"] is True

    assert patron3.is_blocked
    note = patron3.patron.get("blocked_note")
    assert note and note in patron3.get_blocked_message()


def test_blocked_field_not_present(client, librarian_martigny, patron2_martigny):
    """Test ptrn7 do not have any blocked field."""
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for("invenio_records_rest.ptrn_item", pid_value=patron2_martigny.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert "blocked" not in data["metadata"]["patron"]


def test_blocked_patron_cannot_request(
    client,
    librarian_martigny,
    item_lib_martigny,
    lib_martigny,
    patron_martigny,
    patron3_martigny_blocked,
    circulation_policies,
):
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(
        url_for(
            "api_item.can_request",
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron3_martigny_blocked.get("patron", {}).get("barcode")[0],
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data["can"]

    # Check with valid patron
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
    assert data["can"]

    # Create "virtual" Loan (not registered)
    loan = Loan(
        {
            "item_pid": item_pid_to_object(item_lib_martigny.pid),
            "library_pid": lib_martigny.pid,
            "patron_pid": patron3_martigny_blocked.pid,
        }
    )
    assert not can_be_requested(loan)
