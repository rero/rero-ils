# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022-2023 RERO
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

"""User api tests."""

import string

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json


def test_generate_password(client, app, librarian_martigny):
    """Test entrypoint generate password."""
    app.config['RERO_ILS_PASSWORD_MIN_LENGTH'] = 8
    app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR'] = False

    # Not Logged
    res = client.get(url_for('api_user.password_generate'))
    assert res.status_code == 401

    # Logged as librarian
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for('api_user.password_generate', length=6))
    assert res.status_code == 400
    assert get_json(res)['message'] \
        .find('The password must be at least 8 characters long.') != -1

    res = client.get(url_for('api_user.password_generate'))
    assert res.status_code == 200
    assert len(res.get_data(as_text=True)) == 8

    res = client.get(url_for('api_user.password_generate', length=12))
    assert res.status_code == 200
    assert len(res.get_data(as_text=True)) == 12

    app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR'] = True
    res = client.get(url_for('api_user.password_generate'))
    assert res.status_code == 200
    assert set(string.punctuation).intersection(res.get_data(as_text=True))

    res = client.get(url_for('api_user.password_generate', length=2))
    assert res.status_code == 400


def test_validate_password(client, app):
    """Test entrypoint validate password."""
    app.config['RERO_ILS_PASSWORD_MIN_LENGTH'] = 8
    app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR'] = False

    res = client.post(url_for('api_user.password_validate'), json={})
    assert get_json(res)['message'] \
        .find('The password must be filled in') != -1
    assert res.status_code == 400

    res = client.post(
        url_for('api_user.password_validate'), json={'password': 'foo'})
    assert get_json(res)['message'] \
        .find('Field must be at least 8 characters long.') != -1
    assert res.status_code == 400

    res = client.post(
        url_for('api_user.password_validate'), json={'password': '12345678'})
    assert get_json(res)['message'] \
        .find('The password must contain a lower case character.') != -1
    assert res.status_code == 400

    res = client.post(
        url_for('api_user.password_validate'), json={'password': 'a2345678'})
    assert get_json(res)['message'] \
        .find('The password must contain a upper case character.') != -1
    assert res.status_code == 400

    res = client.post(
        url_for('api_user.password_validate'), json={'password': 'aaaaPPPP'})
    assert get_json(res)['message'] \
        .find('The password must contain a number.') != -1
    assert res.status_code == 400

    res = client.post(
        url_for('api_user.password_validate'), json={'password': 'FooBar123'})
    assert res.status_code == 200

    app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR'] = True
    res = client.post(
        url_for('api_user.password_validate'), json={'password': 'FooBar123'})
    assert get_json(res)['message'] \
        .find('The password must contain a special character.') != -1
    assert res.status_code == 400

    res = client.post(
        url_for('api_user.password_validate'), json={'password': 'FooBar123$'})
    assert res.status_code == 200
