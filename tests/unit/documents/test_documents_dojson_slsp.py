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

"""DOJSON module tests."""

from __future__ import absolute_import, print_function

import mock
from dojson.contrib.marc21.utils import create_record

from rero_ils.modules.documents.dojson.contrib.marc21tojson.slsp import marc21


@mock.patch('requests.Session.get')
def test_marc21_to_contribution(mock_get):
    """Test dojson marc21_to_contribution."""
    marc21xml = """
    <record>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Jean-Paul</subfield>
        <subfield code="b">II</subfield>
        <subfield code="c">Pape</subfield>
        <subfield code="d">1954-</subfield>
        <subfield code="4">aut</subfield>
      </datafield>
      <datafield tag="240" ind1=" " ind2=" ">
        <subfield code="a">Treaties, etc.</subfield>
      </datafield>
      <datafield tag="700" ind1=" " ind2=" ">
        <subfield code="a">Dumont, Jean</subfield>
        <subfield code="c">Historien</subfield>
        <subfield code="d">1921-2014</subfield>
        <subfield code="4">edt</subfield>
      </datafield>
      <datafield tag="700" ind1="1" ind2=" ">
        <subfield code="a">Santamaría, Germán</subfield>
        <subfield code="t">No morirás</subfield>
        <subfield code="l">français</subfield>
      </datafield>
      <datafield tag="710" ind1=" " ind2=" ">
        <subfield code="a">RERO</subfield>
      </datafield>
      <datafield tag="711" ind1="2" ind2=" ">
        <subfield code="a">Biennale de céramique contemporaine</subfield>
        <subfield code="n">(17 :</subfield>
        <subfield code="d">2003 :</subfield>
        <subfield code="c">Châteauroux)</subfield>
      </datafield>
      <datafield tag="730" ind1="0" ind2=" ">
        <subfield code="a">Bible.</subfield>
        <subfield code="n">000.</subfield>
        <subfield code="p">A.T. et N.T. :</subfield>
        <subfield code="l">Coréen</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('contribution') == [{
        'entity': {
            'type': 'bf:Person',
            'authorized_access_point': 'Jean-Paul II, Pape, 1954'
        },
        'role': ['aut']
    }, {
        'entity': {
            'type': 'bf:Person',
            'authorized_access_point': 'Dumont, Jean, 1921-2014, Historien'
        },
        'role': ['edt']
    }, {
        'entity': {
            'type': 'bf:Organisation',
            'authorized_access_point': 'RERO'
        },
        'role': ['ctb']
    }, {
        'entity': {
            'type': 'bf:Organisation',
            'authorized_access_point':
                'Biennale de céramique contemporaine (17 : 2003 : Châteauroux)'
        },
        'role': ['aut']
    }]
    assert data.get('work_access_point') == [{
        'creator': {
            'date_of_birth': '1954',
            'numeration': 'II',
            'preferred_name': 'Jean-Paul',
            'qualifier': 'Pape',
            'type': 'bf:Person'
        },
        'title': 'Treaties, etc.'
    }, {
        'creator': {
            'preferred_name': 'Santamaría, Germán',
            'type': 'bf:Person'
        },
        'language': 'fre',
        'title': 'No morirás'
    }, {
        'miscellaneous_information': 'language: Coréen',
        'part': [{
            'partName': 'A.T. et N.T.',
            'partNumber': '000'
        }],
        'title': 'Bible'
    }]

    marc21xml = """
    <record>
      <datafield tag="700" ind1="1" ind2=" ">
        <subfield code="a">Santamaría, Germán</subfield>
        <subfield code="t">No morirás</subfield>
        <subfield code="d">1919-1990</subfield>
      </datafield>
      <datafield tag="700" ind1="1" ind2=" ">
        <subfield code="a">Santamaría, Germán</subfield>
        <subfield code="t">No morirás</subfield>
        <subfield code="d">1919-</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get('work_access_point') == [{
        'creator': {
            'date_of_birth': '1919',
            'date_of_death': '1990',
            'preferred_name': 'Santamaría, Germán',
            'type': 'bf:Person'
        },
        'title': 'No morirás'
    }, {
        'creator': {
            'date_of_birth': '1919',
            'preferred_name': 'Santamaría, Germán',
            'type': 'bf:Person'
        },
        'title': 'No morirás'
    }]
