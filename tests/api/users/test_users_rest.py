# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2023 RERO
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


def test_users_post_put(client, user_data_tmp, librarian_martigny,
                        json_header, default_user_password):
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
    # test with invalid password
    user_data_tmp['first_name'] = 1
    user_data_tmp['password'] = '12345'
    res, data = postdata(
        client,
        'api_users.users_list',
        user_data_tmp
    )
    assert res.status_code == 400

    # test with invalid first_name
    user_data_tmp['first_name'] = 1
    user_data_tmp['password'] = default_user_password
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

    # test invalid password
    user_data_tmp['first_name'] = 'Johnny'
    user_data_tmp['password'] = '1234'
    res = client.put(
        url_for(
            'api_users.users_item',
            id=2),
        data=json.dumps(user_data_tmp),
        headers=json_header
    )
    assert res.status_code == 400

    # test valid password
    user_data_tmp['password'] = 'Pw123456'
    res = client.put(
        url_for(
            'api_users.users_item',
            id=2),
        data=json.dumps(user_data_tmp),
        headers=json_header
    )
    assert res.status_code == 200


def test_users_search_api(
        client, librarian_martigny, patron_martigny, user_without_profile):
    """Test users search REST API."""
    l_martigny = librarian_martigny
    librarian_martigny = librarian_martigny.dumps()
    p_martigny = patron_martigny
    patron_martigny = patron_martigny.dumps()

    res = client.get(
        url_for(
            'api_users.users_list',
            q=''
        )
    )
    assert res.status_code == 401

    login_user_via_session(client, l_martigny.user)
    # empty query => no result
    res = client.get(
        url_for(
            'api_users.users_list'
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'] == []
    assert hits['hits']['total']['value'] == 0

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
    assert hits['hits']['hits'][0]['metadata']['username'] == \
        patron_martigny['username']
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
    assert hits['hits']['hits'][0]['metadata']['username'] == \
        patron_martigny['username']
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
    assert hits['hits']['hits'][0]['metadata']['username'] == \
        patron_martigny['username']
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
    assert hits['hits']['hits'][0]['metadata']['username'] == \
        patron_martigny['username']
    assert hits['hits']['total']['value'] == 1

    # non patron by email
    res = client.get(
        url_for(
            'api_users.users_list',
            q='email:' + user_without_profile.email
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'][0]['metadata']['email'] == \
        user_without_profile.email
    assert hits['hits']['total']['value'] == 1

    # by uppercase email
    res = client.get(
        url_for(
            'api_users.users_list',
            q='email:' + patron_martigny['email'].upper()
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert hits['hits']['hits'][0]['metadata']['username'] == \
        patron_martigny['username']
    assert hits['hits']['total']['value'] == 1

    # Login with patron role
    login_user_via_session(client, p_martigny.user)
    res = client.get(
        url_for(
            'api_users.users_list',
            q=patron_martigny['username']
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert 'metadata' not in hits['hits']['hits'][0]
    assert hits['hits']['hits'][0]['id'] == patron_martigny['user_id']

    res = client.get(
        url_for(
            'api_users.users_item',
            id=p_martigny.user.id
        )
    )
    assert res.status_code == 200
    record = get_json(res)
    assert patron_martigny['username'] == record.get('metadata', [])\
        .get('username')

    # Login with librarian role
    login_user_via_session(client, l_martigny.user)
    res = client.get(
        url_for(
            'api_users.users_list',
            q=patron_martigny['username']
        )
    )
    assert res.status_code == 200
    hits = get_json(res)
    assert 'metadata' in hits['hits']['hits'][0]
    assert hits['hits']['hits'][0]['metadata']['username'] == \
        patron_martigny['username']
