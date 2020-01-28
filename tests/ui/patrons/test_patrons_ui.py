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


from urllib.parse import unquote

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, to_relative_url


def test_patrons_profile(
        client, librarian_martigny_no_email, loan_pending_martigny,
        lib_martigny, patron_martigny_no_email, loc_public_martigny,
        item_type_standard_martigny, item_lib_martigny, json_header,
        circ_policy_short_martigny):
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

    # create patron transactions
    data = {
        'patron_pid': patron_martigny_no_email.pid,
        'item_pid': item_lib_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    loan = item_lib_martigny.request(**data)
    loan_pid = loan[1].get('request').get('pid')

    loan = item_lib_martigny.checkout(**data)

    # patron visits his profile to list checked-out items
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(url_for('patrons.profile'))
    assert res.status_code == 200

    # patron successfully renew the item
    res = client.post(
        url_for('patrons.profile'),
        data={'loan_pid': loan_pid}
    )
    assert res.status_code == 200

    # disable possiblity to renew the item
    circ_policy_short_martigny['number_renewals'] = 0
    circ_policy_short_martigny.update(
        circ_policy_short_martigny, dbcommit=True, reindex=True)

    # patron fails to renew the item
    res = client.post(
        url_for('patrons.profile'),
        data={'loan_pid': loan_pid}
    )
    assert res.status_code == 200

    # checkin item to create history for this patron
    data['transaction_location_pid'] = loc_public_martigny.pid
    data['pid'] = loan_pid
    loan = item_lib_martigny.checkin(**data)

    # patron visits his profile to list history items
    login_user_via_session(client, patron_martigny_no_email.user)
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
