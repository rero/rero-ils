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

"""Tests UI view for users."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_users_not_authorized_access(client):
    """Test profile or change password if the user is not logged."""

    res = client.get(url_for("users.profile", viewcode="global"))
    assert res.status_code == 401

    res = client.get(url_for("users.password", viewcode="global"))
    assert res.status_code == 401


def test_users_authorized_access(client, patron_martigny):
    """Test profile and change password if the user is logged."""

    login_user_via_session(client, patron_martigny.user)
    res = client.get(url_for("users.profile", viewcode="global"))
    assert res.status_code == 200

    res = client.get(url_for("users.password", viewcode="global"))
    assert res.status_code == 200


def test_users_readonly_not_authorized_access(app, client, patron_martigny):
    """Test profile and change password with readonly config."""

    app.config["RERO_PUBLIC_USERPROFILES_READONLY"] = True
    login_user_via_session(client, patron_martigny.user)
    res = client.get(url_for("users.profile", viewcode="global"))
    assert res.status_code == 401

    res = client.get(url_for("users.password", viewcode="global"))
    assert res.status_code == 401
