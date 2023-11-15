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

"""Test translations API."""
from flask import url_for
from utils import get_json


def test_translations(client, app):
    """Test translations API."""

    for ln in app.extensions.get('invenio-i18n').get_languages():
        res = client.get(
            url_for(
                'api_blueprint.translations',
                ln=ln[0]
            )
        )
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
    res = client.get(
        url_for(
            'api_blueprint.translations',
            ln='dummy_language'
        )
    )
    assert res.status_code == 404

    res = client.get(
        url_for(
            'api_blueprint.translations',
            ln='doesnotexists'
        )
    )
    assert res.status_code == 404
