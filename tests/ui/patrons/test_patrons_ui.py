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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests UI view for patrons."""


from urllib.parse import unquote

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, to_relative_url


def test_patrons_profile(
        client, librarian_martigny_no_email, loan_pending_martigny):
    """Test patron profile."""
    # check redirection
    res = client.get(url_for('patrons.profile'))
    assert res.status_code == 302
    assert to_relative_url(res.location) == unquote(url_for(
        'security.login', next='/global/patrons/profile'))

    # check with logged user
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(url_for('patrons.profile'))
    assert res.status_code == 200


def test_patrons_logged_user(client, librarian_martigny_no_email):
    """Test logged user info API."""
    res = client.get(url_for('patrons.logged_user'))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')
    assert data.get('settings').get('language')

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.patrons.views.current_i18n',
        current_i18n
    ):
        login_user_via_session(client, librarian_martigny_no_email.user)
        res = client.get(url_for('patrons.logged_user'))
        assert res.status_code == 200
        data = get_json(res)
        assert data.get('metadata') == librarian_martigny_no_email
        assert data.get('settings').get('language') == 'fr'
