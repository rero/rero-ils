# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Tests acquisition serializers."""

from api.acquisition.acq_utils import _del_resource, _make_resource
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.utils import get_ref_for_pid


def test_acquisition_orders_serializers(
    client,
    librarian_martigny,
    budget_2020_martigny,
    lib_martigny,
    vendor_martigny,
    document,
    rero_json_header,
):
    """Test orders serializer."""
    login_user_via_session(client, librarian_martigny.user)
    # STEP 0 :: Create the account with multiple order lines
    account_data = {
        "name": "Account A",
        "allocated_amount": 1000,
        "budget": {"$ref": get_ref_for_pid("budg", budget_2020_martigny.pid)},
        "library": {"$ref": get_ref_for_pid("lib", lib_martigny.pid)},
    }
    account_a = _make_resource(client, "acac", account_data)
    account_a_ref = {"$ref": get_ref_for_pid("acac", account_a.pid)}
    order_data = {
        "vendor": {"$ref": get_ref_for_pid("vndr", vendor_martigny.pid)},
        "library": {"$ref": get_ref_for_pid("lib", lib_martigny.pid)},
        "reference": "ORDER#1",
    }
    order = _make_resource(client, "acor", order_data)
    order.reindex()
    line_data = {
        "acq_account": account_a_ref,
        "acq_order": {"$ref": get_ref_for_pid("acor", order.pid)},
        "document": {"$ref": get_ref_for_pid("doc", document.pid)},
        "quantity": 4,
        "amount": 25,
    }
    order_line_1 = _make_resource(client, "acol", line_data)

    # TEST ORDER SERIALIZER
    list_url = url_for("invenio_records_rest.acor_list")
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    record = data.get("hits", {}).get("hits", [])[0]
    assert (
        record.get("metadata", {})
        .get("order_lines", [])[0]
        .get("account", {})
        .get("name")
        == account_a["name"]
    )
    assert (
        record.get("metadata", {})
        .get("order_lines", [])[0]
        .get("document", {})
        .get("pid")
        == document.pid
    )

    # RESET RESOURCES
    _del_resource(client, "acol", order_line_1.pid)
    _del_resource(client, "acor", order.pid)
    _del_resource(client, "acac", account_a.pid)
