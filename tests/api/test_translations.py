# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test translations API."""

from flask import url_for

from tests.utils import get_json


def test_translations(client, app):
    """Test translations API."""

    for ln in app.extensions.get("invenio-i18n").get_languages():
        res = client.get(url_for("api_blueprint.translations", ln=ln[0]))
        assert res.status_code == 200
        assert len(get_json(res)) > 0


def test_translations_exceptions(client, app):
    """Test exceptions raised by translations API."""

    # Note : usage of type()
    #   the usage of `type` allow to create on the fly a class with only
    #   necessary attributes for the mock. In the Below case, we could replace
    #   the type(...) by :
    #
    #   ... class FakeDomain(object):
    #   ...     paths = []
    #
    res = client.get(url_for("api_blueprint.translations", ln="dummy_language"))
    assert res.status_code == 404

    res = client.get(url_for("api_blueprint.translations", ln="doesnotexists"))
    assert res.status_code == 404
