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

from flask import url_for

from rero_ils.views import nl2br


def test_nl2br():
    """Test nl2br function view."""
    assert 'foo<br>Bar' == nl2br('foo\nBar')


def test_schemaform(client):
    """Test schema form."""
    result = client.get(url_for(
        'rero_ils.schemaform', document_type="documents"))
    assert result.status_code == 200

    result = client.get(url_for(
        'rero_ils.schemaform', document_type="not_exists"))
    assert result.status_code == 404
