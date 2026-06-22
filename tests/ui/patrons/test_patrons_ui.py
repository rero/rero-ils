# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests UI view for patrons."""

from unittest import mock

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import get_json


def test_patrons_logged_user(client, librarian_martigny):
    """Test logged user info API."""

    # No logged user (only settings are present)
    res = client.get(url_for("patrons.logged_user"))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get("metadata")
    assert not data.get("patrons")
    assert data.get("settings")

    # logged user
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for("patrons.logged_user", resolve=1))
    assert res.status_code == 200
    data = get_json(res)
    assert data.get("user")
    assert data.get("user", {}).get("id")
    assert data.get("user", {}).get("first_name")
    assert data.get("user", {}).get("last_name")
    assert data.get("patrons")
    assert data.get("settings")
    assert data.get("permissions")
    assert data.get("patrons")[0].get("organisation")
    available_languages = data.get("settings").get("availableLanguages")
    assert available_languages[0] == {"code": "en", "name": "English"}
    assert {"code": "fr", "name": "French"} in available_languages

    class current_i18n:
        class locale:
            language = "fr"

    with mock.patch("rero_ils.modules.patrons.views.current_i18n", current_i18n):
        login_user_via_session(client, librarian_martigny.user)
        res = client.get(url_for("patrons.logged_user"))
        assert res.status_code == 200
        data = get_json(res)
        assert (
            data.get("patrons")[0]["libraries"][0]["pid"]
            == librarian_martigny["libraries"][0]["$ref"].rsplit("/", 1)[-1]
        )
        assert data.get("settings").get("language") == "fr"
        assert data.get("settings").get("globalView") == "global"
        assert data.get("settings").get("maxFilesCount") == 600
