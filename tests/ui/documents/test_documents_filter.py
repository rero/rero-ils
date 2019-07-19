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
