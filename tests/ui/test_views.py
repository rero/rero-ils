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

"""Views tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import session, url_for
from flask_login import login_user, logout_user
from utils import postdata

from rero_ils.theme.views import nl2br


def test_nl2br():
    """Test nl2br function view."""
    assert 'foo<br>Bar' == nl2br('foo\nBar')


def test_error(client):
    """Test error entrypoint."""
    with pytest.raises(Exception):
        client.get(url_for(
            'rero_ils.error'
        ))


def test_schemaform(client):
    """Test schema form."""
    result = client.get(url_for(
        'rero_ils.schemaform', document_type="documents"))
    assert result.status_code == 200

    result = client.get(url_for(
        'rero_ils.schemaform', document_type="not_exists"))
    assert result.status_code == 404


def test_organisation_link_on_homepage(client):
    """Test Organisation link on homepage."""
    result = client.get(url_for(
        'rero_ils.index'
    ))
    assert result.status_code == 200
    assert str(result.data).find('RERO+ catalogue') > -1


def test_global_link_on_institution_homepage(client, org_martigny):
    """Test global link on institution homepage."""
    result = client.get(url_for(
        'rero_ils.index_with_view_code',
        viewcode='org1'
    ))
    assert result.status_code == 200
    assert str(result.data).find('Global') > -1


def test_view_parameter_exists(client):
    """Test view parameter exception."""
    result = client.get(url_for(
        'rero_ils.index_with_view_code',
        viewcode='global'
    ))
    assert result.status_code == 302


def test_view_parameter_cypress(client):
    """Test view parameter with cypress viewcode."""
    result = client.get(url_for(
        'rero_ils.index_with_view_code',
        viewcode='cypress'
    ))
    assert result.status_code == 404


def test_view_parameter_notfound(client):
    """Test view parameter exception."""
    result = client.get(url_for(
        'rero_ils.index_with_view_code',
        viewcode='foo'
    ))
    assert result.status_code == 404


def test_external_endpoint_on_institution_homepage(client, org_martigny, app):
    """Test external endpoint on institution homepage."""
    result = client.get(url_for(
        'rero_ils.index_with_view_code',
        viewcode='org1'
    ))
    endpoint = app.config['RERO_ILS_THEME_ORGANISATION_CSS_ENDPOINT']
    assert endpoint == "https://resources.rero.ch/bib/test/css/"
    assert str(result.data).find(endpoint) > 1


def test_help(client):
    """Test help entrypoint."""
    result = client.get(url_for('wiki.index'))
    assert result.status_code == 302


# TODO: uncomment tests when rero-ils-ui is deployed on npm
# def test_search_no_parameter(client):
#     """Test search entrypoint."""
#     result = client.get(url_for(
#         'rero_ils.search', recordType='document', viewcode='global'))
#     assert result.status_code == 302


# def test_search_with_parameters(client):
#     """Test search entrypoint with parameters."""
#     result = client.get(url_for(
#         'rero_ils.search',
#         recordType='document',
#         viewcode='global',
#         q='',
#         size=20,
#         page=1
#         ))
#     assert result.status_code == 200


def test_language(client, app):
    """Test the language endpoint."""
    res, data = postdata(
        client,
        'rero_ils.set_language',
        dict(
            lang='fr'
        )
    )
    assert session[app.config['I18N_SESSION_KEY']] == 'fr'
    assert data == dict(lang='fr')
    assert res.status_code == 200

    res, data = postdata(
        client,
        'rero_ils.set_language',
        dict(
            lang='it'
        )
    )
    assert session[app.config['I18N_SESSION_KEY']] == 'it'

    res, data = postdata(
        client,
        'rero_ils.set_language',
        dict(
            language='fr'
        )
    )
    assert res.status_code == 400

    res, data = postdata(
        client,
        'rero_ils.set_language',
        dict(
            lang='foo'
        )
    )
    assert res.status_code == 400

    # session is unchanged
    assert session[app.config['I18N_SESSION_KEY']] == 'it'


def test_set_user_name(
        app, librarian_martigny, patron_martigny, user_with_profile,
        user_without_email):
    """Test the user_name in the flask session."""
    # should be the email address
    login_user(user=user_with_profile)
    assert 'user_name' in session
    assert session['user_name'] == user_with_profile.email
    # should be removed
    logout_user()
    assert 'user_name' not in session

    # should not be set
    login_user(user=user_without_email)
    assert 'user_name' not in session
    logout_user()

    # should be the formatted name
    login_user(user=patron_martigny.user)
    assert session['user_name'] == patron_martigny.formatted_name
    logout_user()

    # should be the formatted name
    login_user(user=librarian_martigny.user)
    assert session['user_name'] == librarian_martigny.formatted_name
    logout_user()


def test_google_analytics(client, app):
    """Testing the insertion of the google analytics code in the html page."""
    # The Google Analytics code must not be present on the page.
    result = client.get(url_for('rero_ils.index'))
    assert 'gtag' not in result.text

    # The Google Analytics code must be present on the page.
    app.config['RERO_ILS_GOOGLE_ANALYTICS_TAG_ID'] = 'GA-Foo'
    result = client.get(url_for('rero_ils.index'))
    assert 'gtag' in result.text
