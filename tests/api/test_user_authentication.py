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

"""Test User Authentication API."""
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata


def test_login(client, patron_sion_no_email):
    """Test login with several scenarios."""

    # user does not exists
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': 'not@exist.com',
            'password': ''
        }
    )
    assert res.status_code == 400
    data = get_json(res)
    assert data['errors'][0] == dict(
        field='email', message='USER_DOES_NOT_EXIST')

    # wrong password
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion_no_email.get('email'),
            'password': 'bad'
        }
    )
    assert res.status_code == 400
    data = get_json(res)
    assert data['errors'][0] == dict(
        field='password', message='Invalid password')

    # login by email
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion_no_email.get('email'),
            'password': patron_sion_no_email.get('birth_date')
        }
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('id')
    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))

    # login by username
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion_no_email.get('username'),
            'password': patron_sion_no_email.get('birth_date')
        }
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('id')
    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))


def test_login_without_email(client, patron_sion_without_email):
    """Test login with several scenarios."""
    # login by username without email
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion_without_email.get('username'),
            'password': patron_sion_without_email.get('birth_date')
        }
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('id')
    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))


def test_change_password(client, patron_martigny_no_email,
                         librarian_sion_no_email,
                         librarian_martigny_no_email):
    """Test login with several scenarios."""

    # try to change password with an anonymous user
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': patron_martigny_no_email.get('birth_date'),
            'new_password': 'new'
        }
    )
    data = get_json(res)
    assert res.status_code == 401

    # with a logged but the password is too short
    login_user_via_session(client, patron_martigny_no_email.user)
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': patron_martigny_no_email.get('birth_date'),
            'new_password': 'new'
        }
    )
    data = get_json(res)
    assert res.status_code == 400
    assert data.get('message') == 'Validation error.'

    # with a logged user
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': patron_martigny_no_email.get('birth_date'),
            'new_password': 'new_passwd'
        }
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('message') == 'You successfully changed your password.'

    # with a librarian of a different organisation
    login_user_via_session(client, librarian_sion_no_email.user)
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'username': patron_martigny_no_email.get('username'),
            'new_password': 'new_passwd2'
        }
    )
    data = get_json(res)
    assert res.status_code == 401

    # with a librarian of the same organisation
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'username': patron_martigny_no_email.get('username'),
            'new_password': 'new_passwd2'
        }
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('message') == 'You successfully changed your password.'

    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))
