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

"""Views tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import url_for

from rero_ils.views import nl2br


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
    assert str(result.data).find('Institutions') > -1


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
    assert result.status_code == 200


def test_view_parameter_notfound(client):
    """Test view parameter exception."""
    result = client.get(url_for(
        'rero_ils.index_with_view_code',
        viewcode='foo'
    ))
    assert result.status_code == 404


def test_help(client):
    """Test help entrypoint."""
    result = client.get(url_for('rero_ils.help'))
    assert result.status_code == 302


def test_search_no_parameter(client):
    """Test search entrypoint."""
    result = client.get(url_for(
        'rero_ils.search', recordType='document', viewcode='global'))
    assert result.status_code == 302


def test_search_with_parameters(client):
    """Test search entrypoint with parameters."""
    result = client.get(url_for(
        'rero_ils.search',
        recordType='document',
        viewcode='global',
        q='',
        size=20,
        page=1
        ))
    assert result.status_code == 200
