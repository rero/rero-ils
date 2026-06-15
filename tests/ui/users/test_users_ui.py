# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests UI view for users."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_users_not_authorized_access(client):
    """Test profile or change password if the user is not logged. Redirected to the login page."""

    res = client.get(url_for("patrons.profile", viewcode="global", path="user/edit"))
    assert res.status_code == 302

    res = client.get(url_for("patrons.profile", viewcode="global", path="password/edit"))
    assert res.status_code == 302


def test_users_authorized_access(client, patron_martigny):
    """Test profile and change password if the user is logged."""

    login_user_via_session(client, patron_martigny.user)
    res = client.get(url_for("patrons.profile", viewcode="global", path="user/edit"))
    assert res.status_code == 200

    res = client.get(url_for("patrons.profile", viewcode="global", path="password/edit"))
    assert res.status_code == 200


def test_user_profile_authorization(app, client, librarian_martigny):
    """Test profile and change password with readonly config."""

    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for("patrons.profile", viewcode="global"))
    assert res.status_code == 401
    res = client.get(url_for("patrons.profile", viewcode="global", path="user/edit"))
    assert res.status_code == 200

    res = client.get(url_for("patrons.profile", viewcode="global", path="password/edit"))
    assert res.status_code == 200


def test_users_readonly_not_authorized_access(app, client, patron_martigny):
    """Test profile and change password with readonly config."""

    app.config["RERO_ILS_PUBLIC_USERPROFILES_READONLY"] = True
    login_user_via_session(client, patron_martigny.user)
    res = client.get(url_for("patrons.profile", viewcode="global", path="user/edit"))
    assert res.status_code == 401

    res = client.get(url_for("patrons.profile", viewcode="global", path="password/edit"))
    assert res.status_code == 401
    app.config["RERO_ILS_PUBLIC_USERPROFILES_READONLY"] = False
