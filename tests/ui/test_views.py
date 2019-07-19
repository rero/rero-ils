# -*- coding: utf-8 -*-
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
