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

"""Users Record tests."""

from __future__ import absolute_import, print_function

import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata


def test_users_api(
    client, user_data_tmp, librarian_martigny, json_header):
    """Test users REST api for retrieve, create and update."""
    first_name = user_data_tmp.get('first_name')

    # test unauthorized create
    user_data_tmp['toto'] = 'toto'
    res, data = postdata(
        client,
        'api_users.users_list',
        user_data_tmp
    )
    assert res.status_code == 401

    login_user_via_session(client, librarian_martigny.user)

    # test invalid create
    user_data_tmp['toto'] = 'toto'
    res, data = postdata(
        client,
        'api_users.users_list',
        user_data_tmp
    )
    assert res.status_code == 400


    user_data_tmp.pop('toto')
    user_data_tmp['first_name'] = 1
    res, data = postdata(
        client,
        'api_users.users_list',
        user_data_tmp
    )
    assert res.status_code == 400

    # test valid create
    user_data_tmp['first_name'] = first_name
    res, data = postdata(
        client,
        'api_users.users_list',
        user_data_tmp
    )
    assert res.status_code == 200
    user = get_json(res)
    assert user['id'] == 2
    assert user['metadata']['first_name'] == user_data_tmp.get('first_name')

    # test get
    res = client.get(
        url_for(
            'api_users.users_item',
            id=2
        )
    )
    assert res.status_code == 200
    user = get_json(res)
    assert user['id'] == 2
    assert user['metadata']['first_name'] == user_data_tmp.get('first_name')

    # test valid update
    user_data_tmp['first_name'] = 'Johnny'
    res = client.put(
        url_for(
            'api_users.users_item',
            id=2),
        data=json.dumps(user_data_tmp),
        headers=json_header
    )
    assert res.status_code == 200
    user = get_json(res)
    assert user['id'] == 2
    assert user['metadata']['first_name'] == 'Johnny'

    # test invalid update
    user_data_tmp['first_name'] = 1
    res = client.put(
        url_for(
            'api_users.users_item',
            id=2),
        data=json.dumps(user_data_tmp),
        headers=json_header
    )
    assert res.status_code == 400


def test_users_search_api(client, librarian_martigny, patron_martigny):
    """Test users search REST API."""
    res = client.get(
        url_for(
            'api_users.users_list',
            q=''
        )
    )
    assert res.status_code == 401

    login_user_via_session(client, librarian_martigny.user)
    # empty query => no result
    res = client.get(
        url_for(
            'api_users.users_list',
            q=''
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'] == []
    assert hits['hits']['total']['value'] == 0

    # all by username
    res = client.get(
        url_for(
            'api_users.users_list',
            q=patron_martigny['username']
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'][0]['id'] == patron_martigny['user_id']
    assert hits['hits']['total']['value'] == 1

    # all by email
    res = client.get(
        url_for(
            'api_users.users_list',
            q=patron_martigny['email']
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'][0]['id'] == patron_martigny['user_id']
    assert hits['hits']['total']['value'] == 1

    # by username
    res = client.get(
        url_for(
            'api_users.users_list',
            q='username:' + patron_martigny['username']
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'][0]['id'] == patron_martigny['user_id']
    assert hits['hits']['total']['value'] == 1

    # by email
    res = client.get(
        url_for(
            'api_users.users_list',
            q='email:' + patron_martigny['email']
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'][0]['id'] == patron_martigny['user_id']
    assert hits['hits']['total']['value'] == 1
