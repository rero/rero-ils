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

"""Document filters tests."""


from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.views import abstracts_format, \
    authors_format, publishers_format, series_format


def test_authors_format(db, document_data):
    """Test authors format."""
    result = 'Vincent, Sophie'
    doc = Document.create(document_data, delete_pid=True)
    assert result == authors_format(doc.pid, 'en', 'global')


def test_publishers_format():
    """Test publishers format."""
    result = 'Foo; place1; place2: Foo; Bar'
    assert result == publishers_format([
        {'name': ['Foo']},
        {'place': ['place1', 'place2'], 'name': ['Foo', 'Bar']}
    ])


def test_series_format():
    """Test series format."""
    result = 'serie 1; serie 2, 2018'
    assert result == series_format([
        {'name': 'serie 1'}, {'name': 'serie 2', 'number': '2018'}
    ])


def test_abstracts_format():
    """Test series format."""
    result = 'line1\nline2\nline3'
    assert result == abstracts_format(['line1\n\n\nline2', 'line3'])
