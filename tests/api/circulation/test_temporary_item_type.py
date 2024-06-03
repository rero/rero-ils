# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Tests circulation operation for item with temporary item_type."""
from datetime import datetime, timedelta

import ciso8601
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.utils import get_ref_for_pid


def test_checkout_temporary_item_type(
    client,
    document,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
    circ_policy_short_martigny,
    circ_policy_default_martigny,
):
    """Test checkout or item with temporary item_types"""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # test basic behavior
    cipo_used = CircPolicy.provide_circ_policy(
        lib_martigny.organisation_pid,
        lib_martigny.pid,
        patron_martigny.patron_type_pid,
        item.item_type_circulation_category_pid,
    )
    assert cipo_used == circ_policy_short_martigny

    # add a temporary_item_type on item
    #   due to this change, the cipo used during circulation operation should
    #   be different from the first cipo found.
    item["temporary_item_type"] = {
        "$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)
    }
    item = item.update(data=item, dbcommit=True, reindex=True)

    # check temporary_circulation_category is indexed in document
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        q=f"holdings.circulation_category.pid\
                :{item_type_on_site_martigny.pid}",
    )
    res = client.get(doc_list)
    data = get_json(res)
    assert len(data["hits"]["hits"]) == 1

    cipo_tmp_used = CircPolicy.provide_circ_policy(
        lib_martigny.organisation_pid,
        lib_martigny.pid,
        patron_martigny.patron_type_pid,
        item.item_type_circulation_category_pid,
    )
    assert cipo_tmp_used == circ_policy_default_martigny

    delta = timedelta(cipo_tmp_used.get("checkout_duration"))
    expected_date = datetime.now() + delta
    expected_dates = [expected_date, lib_martigny.next_open(expected_date)]
    expected_dates = [d.strftime("%Y-%m-%d") for d in expected_dates]

    # try a checkout and check the transaction end_date is related to the cipo
    # corresponding to the temporary item_type
    params = dict(
        item_pid=item.pid,
        patron_pid=patron_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
    )
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    transaction_end_date = data["action_applied"]["checkout"]["end_date"]
    transaction_end_date = ciso8601.parse_datetime(transaction_end_date).date()
    transaction_end_date = transaction_end_date.strftime("%Y-%m-%d")
    assert transaction_end_date in expected_dates

    # reset the item to original value
    del item["temporary_item_type"]
    item.update(data=item, dbcommit=True, reindex=True)
