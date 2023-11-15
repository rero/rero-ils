# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Tests Form for users."""

import mock
from bs4 import BeautifulSoup
from flask import url_for


def test_register_form(client, app):
    """Test register form."""
    form_data = {
        'email': 'foo@bar.com',
        'password': '123',
        'password_confirm': '123'
    }
    res = client.post(url_for('security.register'), data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "alert-danger"}).find('p')
    assert 'Field must be at least 8 characters long.' == el.text

    app.config['RERO_ILS_PASSWORD_MIN_LENGTH'] = 10
    form_data = {
        'email': 'foo@bar.com',
        'password': '123',
        'password_confirm': '123'
    }
    res = client.post(url_for('security.register'), data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "alert-danger"}).find('p')
    assert 'Field must be at least 10 characters long.' == el.text

    app.config['RERO_ILS_PASSWORD_MIN_LENGTH'] = 8
    form_data = {
        'email': 'foo@bar.com',
        'password': '12345678',
        'password_confirm': '12345678'
    }
    res = client.post(url_for('security.register'), data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "alert-danger"}).find('p')
    assert el.text == 'The password must contain a lower case character.'

    form_data = {
        'email': 'foo@bar.com',
        'password': 'a12345678',
        'password_confirm': 'a12345678'
    }
    res = client.post(url_for('security.register'), data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "alert-danger"}).find('p')
    assert el.text == 'The password must contain a upper case character.'

    form_data = {
        'email': 'foo@bar.com',
        'password': 'NewHouse',
        'password_confirm': 'NewHouse'
    }
    res = client.post(url_for('security.register'), data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "alert-danger"}).find('p')
    assert el.text == 'The password must contain a number.'

    # Check special char
    app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR'] = True
    form_data = {
        'email': 'foo@bar.com',
        'password': 'House1234',
        'password_confirm': 'House1234'
    }
    res = client.post(url_for('security.register'), data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "alert-danger"}).find('p')
    assert el.text == 'The password must contain a special character.'

    # Valid password
    app.config['RERO_ILS_PASSWORD_SPECIAL_CHAR'] = False
    form_data = {
        'email': 'foo@bar.com',
        'password': 'Pw123456',
        'password_confirm': 'Pw123456'
    }
    res = client.post(url_for('security.register'), data=form_data)
    assert res.status_code == 302
    assert res.location == '/'

    form_data = {
        'email': 'foo@bar.com',
        'password': 'Eléphant$07_',
        'password_confirm': 'Eléphant$07_'
    }
    res = client.post(url_for('security.register'), data=form_data)
    assert res.status_code == 302
    assert res.location == '/'


@mock.patch('flask_security.views.reset_password_token_status',
            mock.MagicMock(
                return_value=[False, False, {'email': 'foo@foo.com'}]))
@mock.patch('flask_security.views.update_password',
            mock.MagicMock())
def test_reset_password_form(client, app):
    """Test reset password form.

    All validator tests are performed by the test_register_form (above).
    Here we only test that the validator is active on the field.
    """

    form_data = {
        'email': 'foo@bar.com',
        'password': '123',
        'password_confirm': '123'
    }
    res = client.post(url_for('security.reset_password', token='123ab'),
                      data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "text-danger"}).find('p')
    assert 'Field must be at least 8 characters long.' == el.text

    form_data = {
        'email': 'foo@bar.com',
        'password': '12345678',
        'password_confirm': '12345678'
    }
    res = client.post(url_for('security.reset_password', token='123ab'),
                      data=form_data)
    soup = BeautifulSoup(res.data, 'html.parser')
    el = soup.find('div', {"class": "text-danger"}).find('p')
    assert el.text == 'The password must contain a lower case character.'
