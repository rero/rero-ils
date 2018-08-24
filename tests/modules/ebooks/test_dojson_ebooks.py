# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""DOJSON transiformation for ebooks module tests."""

from __future__ import absolute_import, print_function

from dojson.contrib.marc21.utils import create_record

from reroils_app.modules.ebooks.dojson.contrib.marc21 import marc21


def test_marc21_to_publishers_ebooks():
    """Test dojson publishers publicationDate."""

    marc21xml = """
    <record>
      <datafield tag="260" ind1=" " ind2=" ">
        <subfield code="a">Lausanne :</subfield>
        <subfield code="b"/>
        <subfield code="c">2015</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('publishers') == [
        {
            'place': ['Lausanne']
        }
    ]


def test_marc21_to_isbn_ebooks():
    """Test dojson publishers publicationDate."""

    marc21xml = """
    <record>
      <datafield tag="020" ind1=" " ind2=" ">
        <subfield code="a">9782812933868</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('identifiers') == {
        'isbn': '9782812933868'
    }

    marc21xml = """
    <record>
      <datafield tag="020" ind1=" " ind2=" ">
        <subfield code="a">feedhttps-www-feedbooks-com-book-414-epub</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert not data.get('identifiers')


def test_marc21_to_languages_ebooks():
    """No languages in ebooks."""
    marc21xml = """
    <record>
        <datafield tag="024" ind1="8" ind2=" ">
            <subfield code="a">http://cantookstation.com/resources/1</subfield>
        </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('languages') == [{'language': 'und'}]


def test_marc21_to_electronic_location_ebooks():
    """Electronic Locations."""
    marc21xml = """
    <record>
      <datafield tag="856" ind1="4" ind2="0">
        <subfield code="u">http://site1.org/resources/1</subfield>
      </datafield>
      <datafield tag="856" ind1="4" ind2="0">
        <subfield code="u">http://site2.org/resources/2</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('electronic_location') == [
        {
            'uri': 'http://site1.org/resources/1'
        }, {
            'uri': 'http://site2.org/resources/2'
        }
    ]


def test_marc21_to_type_ebooks():
    """Electronic Locations."""
    marc21xml = """
    <record>
      <datafield tag="024" ind1="8" ind2=" ">
        <subfield code="a">http://cantookstation.com/resources/1</subfield>
      </datafield>
    </record
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('type') == 'ebook'
