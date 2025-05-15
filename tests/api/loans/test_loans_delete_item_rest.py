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

"""Tests REST API loan deleted item."""

from flask.helpers import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import postdata


def test_loans_serializer_with_deleted_item(
    client,
    item_lib_martigny,
    patron2_martigny,
    librarian_martigny,
    lib_martigny,
    rero_json_header,
    circulation_policies,
):
    """Test loan serializer with a deleted item."""
    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item_lib_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    item_lib_martigny.delete(False, True, True)

    loan_list_url = url_for("invenio_records_rest.loanid_list")
    res = client.get(loan_list_url, headers=rero_json_header)
    assert res.status_code == 200
