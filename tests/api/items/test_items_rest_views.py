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

"""Tests REST API items."""
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.items.api import Item


def test_item_dumps(client, item_lib_martigny, org_martigny,
                    librarian_martigny):
    """Test item dumps and elastic search version."""
    item_dumps = Item(item_lib_martigny.dumps()).replace_refs()

    assert item_dumps.get('organisation').get('pid') == org_martigny.pid

    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    item_es = Item(get_json(res).get('metadata'))
    assert item_es.available
    assert item_es.organisation_pid == org_martigny.pid


def test_patron_checkouts_order(client, librarian_martigny,
                                patron_martigny, loc_public_martigny,
                                item_type_standard_martigny,
                                item3_lib_martigny, json_header,
                                item4_lib_martigny,
                                circulation_policies):
    """Test sort of checkout loans."""
    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item4_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    # sort by transaction_date asc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny.pid,
            sort='_created'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item3_lib_martigny.pid
    assert items[1]['item']['pid'] == item4_lib_martigny.pid

    # sort by transaction_date desc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny.pid,
            sort='-transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item4_lib_martigny.pid
    assert items[1]['item']['pid'] == item3_lib_martigny.pid

    # sort by invalid field
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny.pid,
            sort='does not exist'))
    assert res.status_code == 500
    data = get_json(res)
    assert 'RequestError(400' in data['status']
