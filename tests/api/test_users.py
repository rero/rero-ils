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

"""Test user_info API."""
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json


def test_user_info(
        client, document, user_with_profile, patron_martigny_no_email,
        system_librarian_martigny_no_email):
    """Test users API."""
    # failed: no logged user
    res = client.get(
        url_for(
            'api_blueprint.user_info',
            email_or_username='lroduit@gmail.com'
        )
    )
    assert res.status_code == 401

    # patron should not have the permission
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(
        url_for(
            'api_blueprint.user_info',
            email_or_username='lroduit@gmail.com'
        )
    )
    assert res.status_code == 403

    # librarian
    login_user_via_session(client, system_librarian_martigny_no_email.user)

    # user does not exists
    res = client.get(
        url_for(
            'api_blueprint.user_info',
            email_or_username='does not exists'
        )
    )
    data = get_json(res)
    assert data == {}
    assert res.status_code == 200

    # user already linked to a patron account
    res = client.get(
        url_for(
            'api_blueprint.user_info',
            email_or_username='lroduit@gmail.com'
        )
    )
    data = get_json(res)
    assert data == {}
    assert res.status_code == 200

    # by email
    res = client.get(
        url_for(
            'api_blueprint.user_info',
            email_or_username=user_with_profile.email
        )
    )
    data = get_json(res)
    assert data == {
        'email': user_with_profile.email,
        'city': user_with_profile.profile.city,
        'first_name': user_with_profile.profile.first_name,
        'id': user_with_profile.id,
        'last_name': user_with_profile.profile.last_name,
        'username': user_with_profile.profile.username
    }
    assert res.status_code == 200

    # by user
    res = client.get(
        url_for(
            'api_blueprint.user_info',
            email_or_username=user_with_profile.profile.username
        )
    )
    data = get_json(res)
    assert data == {
        'email': user_with_profile.email,
        'city': user_with_profile.profile.city,
        'first_name': user_with_profile.profile.first_name,
        'id': user_with_profile.id,
        'last_name': user_with_profile.profile.last_name,
        'username': user_with_profile.profile.username
    }
    assert res.status_code == 200
