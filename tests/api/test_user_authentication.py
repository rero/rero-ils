# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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
import re

from flask import url_for
from flask_babel import gettext
from flask_security.recoverable import send_password_reset_notice
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata


def test_login(client, patron_sion, default_user_password):
    """Test login with several scenarios."""
    patron_sion = patron_sion.dumps()
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
    assert data['message'] == 'Invalid user or password'

    # wrong password
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion.get('email'),
            'password': 'bad'
        }
    )
    assert res.status_code == 400
    data = get_json(res)
    assert data['message'] == gettext('INVALID_USER_OR_PASSWORD')

    # login by email
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion.get('email'),
            'password': default_user_password
        }
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('id')
    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))

    # login by username
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion.get('username'),
            'password': default_user_password
        }
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('id')
    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))


def test_login_without_email(client, patron_sion_without_email1,
                             default_user_password):
    """Test login with several scenarios."""
    patron_sion_without_email1 = patron_sion_without_email1.dumps()
    # login by username without email
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.login',
        {
            'email': patron_sion_without_email1.get('username'),
            'password': default_user_password
        }
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('id')
    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))


def test_change_password(client, app, patron_martigny,
                         librarian_sion,
                         librarian_martigny,
                         default_user_password):
    """Test login with several scenarios."""
    # Fix the size of password
    app.config['RERO_ILS_PASSWORD_MIN_LENGTH'] = 8
    p_martigny = patron_martigny
    patron_martigny = patron_martigny.dumps()
    l_sion = librarian_sion
    l_martigny = librarian_martigny
    # try to change password with an anonymous user
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': default_user_password,
            'new_password': default_user_password,
            'new_password_confirm': default_user_password
        }
    )
    data = get_json(res)
    assert res.status_code == 401

    # with a logged but the password is too short
    login_user_via_session(client, p_martigny.user)
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': default_user_password,
            'new_password': '123456',
            'new_password_confirm': '123456'
        }
    )
    data = get_json(res)
    assert res.status_code == 400
    assert data.get('message') == 'Validation error.'
    assert data.get('errors')[0].get('message') == \
        gettext('Field must be at least 8 characters long.')

    # with a logged user
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': default_user_password,
            'new_password': 'Pw123458',
            'new_password_confirm': 'Pw123455'
        }
    )
    data = get_json(res)
    assert res.status_code == 400
    assert data.get('message') == 'Validation error.'
    assert data.get('errors')[0].get('message') == \
        gettext('The 2 passwords are not identical.')

    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'password': default_user_password,
            'new_password': 'Pw123458',
            'new_password_confirm': 'Pw123458'
        }
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('message') == 'You successfully changed your password.'

    # with a librarian of a different organisation
    login_user_via_session(client, l_sion.user)
    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'username': patron_martigny.get('username'),
            'new_password': 'Pw123458',
            'new_password_confirm': 'Pw123458'
        }
    )
    data = get_json(res)
    assert res.status_code == 401

    # with a librarian of the same organisation
    login_user_via_session(client, l_martigny.user)

    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'username': patron_martigny.get('username'),
            'new_password': 'Pw123458',
            'new_password_confirm': 'Pw123455'
        }
    )
    data = get_json(res)
    assert res.status_code == 400
    assert data.get('message') == 'Validation error.'
    assert data.get('errors')[0].get('message') == \
        gettext('The 2 passwords are not identical.')

    res, _ = postdata(
        client,
        'invenio_accounts_rest_auth.change_password',
        {
            'username': patron_martigny.get('username'),
            'new_password': 'Pw123458',
            'new_password_confirm': 'Pw123458'
        }
    )
    data = get_json(res)
    assert res.status_code == 200
    assert data.get('message') == 'You successfully changed your password.'

    # logout for the next test
    client.post(url_for('invenio_accounts_rest_auth.logout'))


def test_patron_reset_notice(patron_martigny, mailbox):
    """Test password reset notice template."""
    send_password_reset_notice(patron_martigny.user)
    assert len(mailbox) == 1
    assert re.search(
        r'Your password has been successfully reset.', mailbox[0].body
    )
    assert re.search(
        r'Best regards', mailbox[0].body
    )
