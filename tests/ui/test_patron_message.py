# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2023 UCLouvain
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

"""Tests message UI view for patrons."""

from bs4 import BeautifulSoup
from flask import url_for
from invenio_accounts.testutils import login_user_via_view


def test_info_message(app, client, patron_martigny, patron_martigny_data,
                      org_martigny_data):
    """Test info message."""
    patron_martigny['patron']['blocked'] = True
    patron_martigny['patron']['blocked_note'] = 'This is a blocked message.'
    patron_martigny['patron']['expiration_date'] = '2022-12-31'
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)

    blocked_message = patron_martigny['patron']['blocked_note']

    # If the user is not identified, there is no user information
    res = client.get('/')
    soup = BeautifulSoup(res.data, 'html.parser')
    assert soup.find('div', {"class": "patron-info-message"}) is None

    login_user_via_view(
        client,
        email=patron_martigny_data['email'],
        password=patron_martigny_data['password'])

    # If the user is identified, we see the name of the organization
    # and the message on the global view
    res = client.get(url_for('rero_ils.index'))
    soup = BeautifulSoup(res.data, 'html.parser')
    li = soup.find('div', {"class": "patron-info-message"}).find('li')

    assert org_martigny_data['name'] == li.find('span').text
    assert f'Your account is currently blocked. Reason: {blocked_message}' \
        == li.find('div', {"class": "message-blocked"}).text
    assert 'Your account has expired. Please contact your library.'\
        == li.find('div', {"class": "message-expired"}).text

    # If the view of the organization, there is no name of it
    res = client.get(url_for(
        'rero_ils.index_with_view_code', viewcode=org_martigny_data['code']))
    soup = BeautifulSoup(res.data, 'html.parser')
    div = soup.find('div', {"class": "patron-info-message"})

    assert div.find('span') is None
    assert f'Your account is currently blocked. Reason: {blocked_message}' \
        == div.find('div', {"class": "message-blocked"}).text
    assert 'Your account has expired. Please contact your library.'\
        == div.find('div', {"class": "message-expired"}).text
