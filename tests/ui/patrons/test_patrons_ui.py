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

"""Tests UI view for patrons."""

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.patrons.views import format_currency_filter


def test_patrons_logged_user(client, librarian_martigny):
    """Test logged user info API."""
    res = client.get(url_for('patrons.logged_user'))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')
    assert data.get('settings').get('language')

    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for('patrons.logged_user', resolve=1))
    assert res.status_code == 200
    data = get_json(res)
    assert 'organisation' in data['metadata']['libraries'][0]

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.patrons.views.current_i18n',
        current_i18n
    ):
        login_user_via_session(client, librarian_martigny.user)
        res = client.get(url_for('patrons.logged_user'))
        assert res.status_code == 200
        data = get_json(res)
        assert data.get('metadata') == librarian_martigny
        assert data.get('settings').get('language') == 'fr'


def test_patrons_logged_user_resolve(
        client,
        librarian_martigny):
    """Test that patron library is resolved in JSON data."""
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for('patrons.logged_user', resolve=1))
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('metadata', {}).get('libraries')


def test_patron_format_currency_filter(app):
    """Test format currency filter."""
    assert format_currency_filter(3, 'EUR') == '€3.00'
    assert format_currency_filter(4.5, 'CHF') == 'CHF4.50'
    assert format_currency_filter(None, 'EUR') is None
