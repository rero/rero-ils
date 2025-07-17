# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2025 RERO+
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

"""Request limits."""

from copy import deepcopy

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.loans.models import LoanAction
from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.utils import get_ref_for_pid


def test_request_library_limit(
    client,
    app,
    lib_martigny,
    patron_type_children_martigny,
    item_lib_martigny,
    item2_lib_martigny,
    item3_lib_martigny,
    item_lib_martigny_data,
    item2_lib_martigny_data,
    item3_lib_martigny_data,
    loc_public_martigny,
    patron_martigny,
    librarian_martigny,
    circ_policy_short_martigny,
):
    """Test requests library limits."""
    patron = patron_martigny
    item2_original_data = deepcopy(item2_lib_martigny_data)
    item3_original_data = deepcopy(item3_lib_martigny_data)
    item1 = item_lib_martigny
    item2 = item2_lib_martigny
    item3 = item3_lib_martigny
    library_ref = get_ref_for_pid("lib", lib_martigny.pid)
    location_ref = get_ref_for_pid("loc", loc_public_martigny.pid)

    login_user_via_session(client, patron_martigny.user)

    # Update fixtures for the tests
    #   * Update the patron_type to set request limits
    #   * All items are linked to the same library/location
    patron_type = patron_type_children_martigny
    patron_type["limits"] = {
        "request_limits": {
            "global_limit": 3,
            "library_limit": 2,
            "library_exceptions": [{"library": {"$ref": library_ref}, "value": 1}],
        }
    }
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    patron_type = PatronType.get_record_by_pid(patron_type.pid)
    item2_lib_martigny_data["location"]["$ref"] = location_ref
    item2.update(item2_lib_martigny_data, dbcommit=True, reindex=True)
    item3_lib_martigny_data["location"]["$ref"] = location_ref
    item3.update(item3_lib_martigny_data, dbcommit=True, reindex=True)

    # First request - All should be fine.
    res, data = postdata(
        client,
        "api_item.patron_request",
        dict(item_pid=item1.pid, pickup_location_pid=loc_public_martigny.pid),
    )
    assert res.status_code == 200
    loan1_pid = data.get("action_applied")[LoanAction.REQUEST].get("pid")

    # Second request
    #   --> The library limit exception should be raised.
    res, data = postdata(
        client,
        "api_item.patron_request",
        dict(item_pid=item2.pid, pickup_location_pid=loc_public_martigny.pid),
    )
    assert res.status_code == 403
    assert "Maximum number of requests for this library reached" in data["message"]

    # remove the library specific exception and try a new request
    #   --> As the limit by library is now '2', the request will be done.
    #   --> Try a third request : the default library_limit exception should
    #       be raised
    patron_type["limits"] = {
        "request_limits": {
            "global_limit": 3,
            "library_limit": 2,
        }
    }
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    res, data = postdata(
        client,
        "api_item.patron_request",
        dict(item_pid=item2.pid, pickup_location_pid=loc_public_martigny.pid),
    )
    assert res.status_code == 200
    loan2_pid = data.get("action_applied")[LoanAction.REQUEST].get("pid")
    res, data = postdata(
        client,
        "api_item.patron_request",
        dict(item_pid=item3.pid, pickup_location_pid=loc_public_martigny.pid),
    )
    assert res.status_code == 403
    assert "Maximum number of requests for this library reached" in data["message"]

    # remove the library default limit and update the global_limit to 2.
    #   --> try the third request : the global_limit exception should now be
    #       raised
    patron_type["limits"] = {"request_limits": {"global_limit": 2}}
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    res, data = postdata(
        client,
        "api_item.patron_request",
        dict(item_pid=item3.pid, pickup_location_pid=loc_public_martigny.pid),
    )
    assert res.status_code == 403
    assert "Maximum number of requests reached" in data["message"]

    login_user_via_session(client, librarian_martigny.user)
    # check the circulation information API
    url = url_for("api_patrons.patron_circulation_informations", patron_pid=patron.pid)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert "error" == data["messages"][0]["type"]
    assert "Maximum number of requests reached" in data["messages"][0]["content"]

    # validate one of the requests to change its status
    #   --> try the third request again, it should still raise the exception
    res, data = postdata(
        client,
        "api_item.validate_request",
        dict(
            pid=loan1_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    res, data = postdata(
        client,
        "api_item.librarian_request",
        dict(
            item_pid=item3.pid,
            patron_pid=patron_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 403
    assert "Maximum number of requests reached" in data["message"]

    # checkout the first request
    #   --> try the third request again, it should now work.
    res, data = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item1.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    assert data.get("action_applied")[LoanAction.CHECKOUT].get("pid") == loan1_pid

    res, data = postdata(
        client,
        "api_item.librarian_request",
        dict(
            item_pid=item3.pid,
            patron_pid=patron_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    loan3_pid = data.get("action_applied")[LoanAction.REQUEST].get("pid")

    # reset fixtures
    #   --> checkin loaned item
    #   --> cancel requests
    #   --> reset patron_type to original value
    #   --> reset items to original values
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item3.pid,
            pid=loan1_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
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
    res, data = postdata(
        client,
        "api_item.cancel_item_request",
        dict(
            pid=loan3_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    del patron_type["limits"]
    patron_type.update(patron_type, dbcommit=True, reindex=True)
    item2.update(item2_original_data, dbcommit=True, reindex=True)
    item3.update(item3_original_data, dbcommit=True, reindex=True)
