#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
