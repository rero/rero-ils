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

"""Tests account rest auth api."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_disabled_endpoint(client, app, patron_martigny):
    """Test disabled endpoint."""

    ext = app.extensions['security']
    ext.registerable = ext.changeable = ext.recoverable = ext.confirmable = \
        True

    app.config['SECURITY_CONFIRMABLE'] = True
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = True
    app.config['ACCOUNTS_SESSION_ACTIVITY_ENABLED'] = True

    def get(url_endpoint):
        res = client.get(url_endpoint)
        assert res.status_code == 404

    def post(url_endpoint):
        res = client.post(url_endpoint)
        assert res.status_code == 404

    post(url_for('invenio_accounts_rest_auth.register'))
    post(url_for('invenio_accounts_rest_auth.forgot_password'))
    post(url_for('invenio_accounts_rest_auth.reset_password'))

    post('invenio_accounts_rest_auth.send_confirmation')
    post('invenio_accounts_rest_auth.confirm_email')

    # Logged as user
    login_user_via_session(client, patron_martigny.user)

    post(url_for('invenio_accounts_rest_auth.logout'))
    get(url_for('invenio_accounts_rest_auth.user_info'))
    get(url_for('invenio_accounts_rest_auth.sessions_list'))
    get(url_for('invenio_accounts_rest_auth.sessions_item', sid_s='1'))
