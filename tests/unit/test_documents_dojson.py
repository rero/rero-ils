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

import os

import mock
from dojson.contrib.marc21.utils import create_record
from utils import mock_response

from rero_ils.modules.documents.dojson.contrib.marc21tojson import marc21tojson
from rero_ils.modules.documents.dojson.contrib.marc21tojson.model import \
    get_mef_person_link
from rero_ils.modules.documents.views import create_publication_statement


# type: leader
def test_marc21_to_type():
    """
    Test dojson marc21_to_type.

    Books: LDR/6-7: am
    Journals: LDR/6-7: as
    Articles: LDR/6-7: aa + add field 773 (journal title)
    Scores: LDR/6: c|d
    Videos: LDR/6: g + 007/0: m|v
    Sounds: LDR/6: i|j
    E-books (imported from Cantook)
    """

    marc21xml = """
    <record>
        <leader>00501nam a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'book'

    marc21xml = """
    <record>
        <leader>00501nas a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'journal'

    marc21xml = """
    <record>
        <leader>00501naa a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'article'

    marc21xml = """
    <record>
        <leader>00501nca a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'score'
    marc21xml = """
    <record>
        <leader>00501nda a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'score'

    marc21xml = """
    <record>
        <leader>00501nia a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'sound'
    marc21xml = """
    <record>
        <leader>00501nja a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'sound'

    marc21xml = """
    <record>
        <leader>00501nga a2200133 a 4500</leader>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('type') == 'video'


# title: 245$a
# without the punctuaction. If there's a $b, then 245$a : $b without the " /"
def test_marc21_to_title():
    """Test dojson marc21_to_title."""

    # subfields $a $b $c
    marc21xml = """
    <record>
      <datafield tag="245" ind1="1" ind2="0">
        <subfield code="a">main title :</subfield>
        <subfield code="b">subtitle /</subfield>
        <subfield code="c">responsability</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('title') == 'main title : subtitle'
    # subfields $a $c
    marc21xml = """
    <record>
      <datafield tag="245" ind1="1" ind2="0">
        <subfield code="a">main title</subfield>
        <subfield code="c">responsability</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('title') == 'main title'
    # subfield $a
    marc21xml = """
    <record>
      <datafield tag="245" ind1="1" ind2="0">
        <subfield code="a">main title</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('title') == 'main title'


# titleProper: [730$a repetitive]
def test_marc21_to_titlesProper():
    """Test dojson marc21titlesProper."""

    marc21xml = """
    <record>
      <datafield tag="730" ind1="1" ind2="0">
        <subfield code="a">proper title</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('titlesProper') == ['proper title']

    marc21xml = """
    <record>
      <datafield tag="730" ind1=" " ind2=" ">
        <subfield code="a">proper title</subfield>
      </datafield>
      <datafield tag="730" ind1=" " ind2=" ">
         <subfield code="a">other proper title</subfield>
       </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('titlesProper') == ['proper title', 'other proper title']


# languages: 008 and 041 [$a, repetitive]
def test_marc21_to_language():
    """Test dojson marc21languages."""

    marc21xml = """
    <record>
      <controlfield tag="008">
        881005s1984    xxu|||||| ||||00|| |ara d
      <controlfield>
      <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">ara</subfield>
        <subfield code="a">eng</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)

    assert data.get('language') == [
        {
            'type': 'bf:Language',
            'value': 'ara'
        },
        {
            'type': 'bf:Language',
            'value': 'eng'
        }
    ]

    marc21xml = """
    <record>
      <controlfield tag="008">
        881005s1984    xxu|||||| ||||00|| |ara d
      <controlfield>
      <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
      </datafield>
      <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">fre</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('language') == [
        {
            'type': 'bf:Language',
            'value': 'ara'
        },       {
            'type': 'bf:Language',
            'value': 'eng'
        },
        {
            'type': 'bf:Language',
            'value': 'fre'
        }
    ]

    marc21xml = """
    <record>
      <datafield tag="041" ind1=" " ind2=" ">
      <subfield code="a">eng</subfield>
    </datafield>
    <controlfield tag="008">
        881005s1984    xxu|||||| ||||00|| |ara d
      <controlfield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)

    assert data.get('language') == [
        {
          'type': 'bf:Language',
          'value': 'ara'
        },
        {
          'type': 'bf:Language',
          'value': 'eng'
        }
    ]

    marc21xml = """
    <record>
      <controlfield tag="008">
        881005s1984    xxu|||||| ||||00|| |ara d
      <controlfield>
      <datafield tag="041" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        <subfield code="a">rus</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('language') == [
        {
           'type': 'bf:Language',
           'value': 'ara'
        },
        {
            'type': 'bf:Language',
            'value': 'eng'
        },
        {
            'type': 'bf:Language',
            'value': 'rus'
        }
    ]

    marc21xml = """
    <record>
      <controlfield tag="008">
        881005s1984    xxu|||||| ||||00|| |ara d
      <controlfield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('language') == [
        {
            'type': 'bf:Language',
            'value': 'ara'
        }
    ]


# authors: loop:
# authors.name: 100$a [+ 100$b if it exists] or
#   [700$a (+$b if it exists) repetitive] or
#   [ 710$a repetitive (+$b if it exists, repetitive)]
# authors.date: 100 $d or 700 $d (facultatif)
# authors.qualifier: 100 $c or 700 $c (facultatif)
# authors.type: if 100 or 700 then person, if 710 then organisation
def test_marc21_to_authors():
    """Test dojson marc21_to_authors."""

    marc21xml = """
    <record>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Jean-Paul</subfield>
        <subfield code="b">II</subfield>
        <subfield code="c">Pape</subfield>
        <subfield code="d">1954-</subfield>
      </datafield>
      <datafield tag="700" ind1=" " ind2=" ">
        <subfield code="a">Dumont, Jean</subfield>
        <subfield code="c">Historien</subfield>
        <subfield code="d">1921-2014</subfield>
      </datafield>
      <datafield tag="710" ind1=" " ind2=" ">
        <subfield code="a">RERO</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    authors = data.get('authors')
    assert authors == [
        {
            'name': 'Jean-Paul II',
            'type': 'person',
            'date': '1954-',
            'qualifier': 'Pape'
        },
        {
            'name': 'Dumont, Jean',
            'type': 'person',
            'date': '1921-2014',
            'qualifier': 'Historien'
        },
        {
            'name': 'RERO',
            'type': 'organisation'
        }
    ]
    marc21xml = """
    <record>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Jean-Paul</subfield>
        <subfield code="b">II</subfield>
        <subfield code="c">Pape</subfield>
        <subfield code="d">1954-</subfield>
      </datafield>
      <datafield tag="700" ind1=" " ind2="2">
        <subfield code="a">Dumont, Jean</subfield>
        <subfield code="c">Historien</subfield>
        <subfield code="d">1921-2014</subfield>
      </datafield>
      <datafield tag="710" ind1=" " ind2=" ">
        <subfield code="a">RERO</subfield>
        <subfield code="c">Martigny</subfield>
        <subfield code="d">1971</subfield>
      </datafield>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    authors = data.get('authors')
    assert authors == [
        {
            'name': 'Jean-Paul II',
            'type': 'person',
            'date': '1954-',
            'qualifier': 'Pape'
        },
        {
            'name': 'RERO',
            'type': 'organisation'
        }
    ]


# Copyright Date: [264 _4 $c non repetitive]
def test_marc21copyrightdate():
    """Test dojson Copyright Date."""

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2="4">
        <subfield code="c">© 1971</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('copyrightDate') == ['© 1971']

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2="4">
        <subfield code="c">© 1971 [extra 1973]</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('copyrightDate') == ['© 1971 [extra 1973]']


def test_marc21_to_provisionActivity_manufacture_date():
    """Test dojson publication statement.
    - 1 manufacture place and 1 agent, 1 manufacture date
    """

    marc21xml = """
      <record>
        <controlfield tag=
          "008">070518s20062010sz ||| |  ||||00|  |fre d</controlfield>
        <datafield tag="041" ind1="0" ind2=" ">
          <subfield code="a">fre</subfield>
          <subfield code="a">ger</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="3">
          <subfield code="a">Bienne :</subfield>
          <subfield code="b">Impr. Weber</subfield>
          <subfield code="c">[2006]</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="4">
          <subfield code="c">© 2006</subfield>
        </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Manufacture',
          'statement': [
              {
                  'label': [
                      {'value': 'Bienne'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Impr. Weber'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'date': '[2006]'
      }
    ]


def test_marc21_to_provisionActivity_canton():
    """Test dojson publication statement.
    - get canton from field 044
    - 3 publication places and 3 agents from one field 264
    """

    marc21xml = """
      <record>
        <controlfield tag=
          "008">070518s20062010sz ||| |  ||||00|  |fre d</controlfield>
        <datafield tag="041" ind1="0" ind2=" ">
          <subfield code="a">fre</subfield>
          <subfield code="a">ger</subfield>
        </datafield>
        <datafield tag="044" ind1=" " ind2=" ">
          <subfield code="a">sz</subfield>
          <subfield code="c">ch-be</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="1">
          <subfield code="a">Biel/Bienne :</subfield>
          <subfield code="b">Centre PasquArt ;</subfield>
          <subfield code="a">Nürnberg :</subfield>
          <subfield code="b">Verlag für Moderne Kunst ;</subfield>
          <subfield code="a">Manchester :</subfield>
          <subfield code="b">distrib. in the United Kingdom [etc.],</subfield>
          <subfield code="c">[2006-2010]</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="3">
          <subfield code="a">Bienne :</subfield>
          <subfield code="b">Impr. Weber</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="4">
          <subfield code="c">© 2006</subfield>
        </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'canton': ['be'],
                  'country': 'sz',
                  'label': [
                      {'value': 'Biel/Bienne'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Centre PasquArt'}
                  ],
                  'type': 'bf:Agent'
              },
              {
                  'label': [
                      {'value': 'Nürnberg'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Verlag für Moderne Kunst'}
                  ],
                  'type': 'bf:Agent'
              },
              {
                  'label': [
                      {'value': 'Manchester'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'distrib. in the United Kingdom [etc.]'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '2006',
          'endDate': '2010',
          'date': '[2006-2010]'
      },
      {
          'type': 'bf:Manufacture',
          'statement': [
              {
                  'label': [
                      {'value': 'Bienne'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Impr. Weber'}
                  ],
                  'type': 'bf:Agent'
              }
          ]
      }
    ]


def test_marc21_to_provisionActivity_1_place_2_agents():
    """Test dojson publication statement.
    - 1 publication place and 2 agents from one field 264
    """

    marc21xml = """
      <record>
        <controlfield tag=
          "008">940202m19699999fr |||||| ||||00|| |fre d</controlfield>
        <datafield tag="264" ind1=" " ind2="1">
          <subfield code="a">[Paris] :</subfield>
          <subfield code="b">Desclée de Brouwer [puis]</subfield>
          <subfield code="b">Etudes augustiniennes,</subfield>
          <subfield code="c">1969-</subfield>
        </datafield>
      </record>
     """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Publication',
        'statement': [
            {
                'country': 'fr',
                'label': [
                    {'value': '[Paris]'}
                ],
                'type': 'bf:Place'
            },
            {
                'label': [
                    {'value': 'Desclée de Brouwer [puis]'}
                ],
                'type': 'bf:Agent'
            },
            {
                'label': [
                    {'value': 'Etudes augustiniennes'}
                ],
                'type': 'bf:Agent'
            }
        ],
        'startDate': '1969',
        'date': '1969-'
    }]


def test_marc21_to_provisionActivity_unknown_place_2_agents():
    """Test dojson publication statement.
    - unknown place and 2 agents from one field 264
    """
    marc21xml = """
      <record>
      <controlfield tag=
        "008">960525s1968    be |||||| ||||00|| |fre d</controlfield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="a">[Lieu de publication non identifié] :</subfield>
        <subfield code="b">Labor :</subfield>
        <subfield code="b">Nathan,</subfield>
        <subfield code="c">1968</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'be',
                  'label': [
                      {'value': '[Lieu de publication non identifié]'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Labor'}
                  ],
                  'type': 'bf:Agent'
              },
              {
                  'label': [
                      {'value': 'Nathan'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '1968',
          'date': '1968'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
        'default': '[Lieu de publication non identifié] : Labor, Nathan, 1968'
    }


def test_marc21_to_provisionActivity_3_places_dann_2_agents():
    """Test dojson publication statement.
    - 3 places and 2 agents from one field 264
    - 2 places with [dann] prefix
    """
    marc21xml = """
      <record>
      <controlfield tag=
        "008">000927m19759999gw |||||| ||||00|  |ger d</controlfield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="a">Hamm (Westf.) ;</subfield>
        <subfield code="a">[dann] Herzberg ;</subfield>
        <subfield code="a">[dann] Nordhausen :</subfield>
        <subfield code="b">T. Bautz,</subfield>
        <subfield code="c">1975-</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'gw',
                  'label': [
                      {'value': 'Hamm (Westf.)'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': '[dann] Herzberg'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': '[dann] Nordhausen'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'T. Bautz'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '1975',
          'date': '1975-'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
        'default': 'Hamm (Westf.) ; [dann] Herzberg ; [dann] Nordhausen : ' +
        'T. Bautz, 1975-'
    }


def test_marc21_to_provisionActivity_2_places_1_agent():
    """Test dojson publication statement.
    - 2 publication places and 1 agents from one field 264
    """

    marc21xml = """
      <record>
      <controlfield tag=
        "008">960525s1966    sz |||||| ||||00|| |fre d</controlfield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="a">[Louvain] ;</subfield>
        <subfield code="a">[Paris] :</subfield>
        <subfield code="b">[éditeur non identifié],</subfield>
        <subfield code="c">[1966]</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'sz',
                  'label': [
                      {'value': '[Louvain]'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': '[Paris]'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': '[éditeur non identifié]'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '1966',
          'date': '[1966]'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
        'default': '[Louvain] ; [Paris] : [éditeur non identifié], [1966]'
    }


def test_marc21_to_provisionActivity_1_place_1_agent_reprint_date():
    """Test dojson publication statement.
    - 1 place and 1 agent from one field 264
    - reprint date in 008
    """
    marc21xml = """
      <record>
      <controlfield tag=
        "008">000918r19161758xxu|||||| ||||00|| |eng d</controlfield>
      <datafield tag="041" ind1="0" ind2=" ">
        <subfield code="a">eng</subfield>
        <subfield code="a">fre</subfield>
      </datafield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="a">Washington :</subfield>
        <subfield code="b">Carnegie Institution of Washington,</subfield>
        <subfield code="c">1916</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'xxu',
                  'label': [
                      {'value': 'Washington'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Carnegie Institution of Washington'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '1916',
          'date': '1916'
      }
    ]


def test_marc21_to_provisionActivity_1_place_1_agent_uncertain_date():
    """Test dojson publication statement.
    - 1 place and 1 agent from one field 264
    - uncertain date
    """
    marc21xml = """
      <record>
      <controlfield tag=
        "008">160126q1941    fr ||| |  ||||00|  |fre d</controlfield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="a">Aurillac :</subfield>
        <subfield code="b">Impr. moderne,</subfield>
        <subfield code="c">[1941?]</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'fr',
                  'label': [
                      {'value': 'Aurillac'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Impr. moderne'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'note': 'Date(s) incertaine(s) ou inconnue(s)',
          'startDate': '1941',
          'date': '[1941?]'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
        'default': 'Aurillac : Impr. moderne, [1941?]'}


def test_marc21_to_provisionActivity_1_place_1_agent_chi_hani():
    """Test dojson publication statement.
    - 1 place and 1 agent from one field 264
    - extract data from the linked 880 from 3 fields 880
    """
    marc21xml = """
      <record>
      <controlfield tag=
        "008">180323s2017    cc ||| |  ||||00|  |chi d</controlfield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="6">880-04</subfield>
        <subfield code="a">Beijing :</subfield>
        <subfield code="b">Beijing da xue chu ban she,</subfield>
        <subfield code="c">2017</subfield>
      </datafield>
      <datafield tag="880" ind1=" " ind2="1">
        <subfield code="6">264-04/$1</subfield>
        <subfield code="a">北京 :</subfield>
        <subfield code="b">北京大学出版社,</subfield>
        <subfield code="c">2017</subfield>
      </datafield>
      <datafield tag="880" ind1="1" ind2=" ">
        <subfield code="6">100-01/$1</subfield>
        <subfield code="a">余锋</subfield>
      </datafield>
      <datafield tag="880" ind1="1" ind2="0">
        <subfield code="6">245-02/$1</subfield>
        <subfield code="a">中国娱乐法 /</subfield>
        <subfield code="c">余锋著</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'cc',
                  'label': [
                      {'value': 'Beijing'},
                      {'value': '北京',
                       'language': 'chi-hani'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Beijing da xue chu ban she'},
                      {'value': '北京大学出版社',
                       'language': 'chi-hani'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '2017',
          'date': '2017'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
      'chi-hani': '北京 : 北京大学出版社, 2017',
      'default': 'Beijing : Beijing da xue chu ban she, 2017'
    }


def test_marc21_to_provisionActivity_1_place_1_agent_ara_arab():
    """Test dojson publication statement.
    - 1 place and 1 agent from one field 264
    - extract data from the linked 880
    """
    marc21xml = """
      <record>
      <controlfield tag=
        "008">150617s2014    ua ||| |  ||||00|  |ara d</controlfield>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="6">880-01</subfield>
        <subfield code="a">al-Qāhirah :</subfield>
        <subfield code="b">Al-Hayʾat al-ʿāmmah li quṣūr al-thaqāfah,</subfield>
        <subfield code="c">2014</subfield>
      </datafield>
      <datafield tag="880" ind1=" " ind2="1">
        <subfield code="6">264-01/(3/r</subfield>
        <subfield code="a">القاهرة :</subfield>
        <subfield code="b">الهيئة العامة لقصور الثقافة,</subfield>
        <subfield code="c">2014</subfield>
      </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'ua',
                  'label': [
                      {'value': 'al-Qāhirah'},
                      {'value': 'القاهرة',
                       'language': 'ara-arab'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Al-Hayʾat al-ʿāmmah li quṣūr ' +
                          'al-thaqāfah'},
                      {'value': 'الهيئة العامة لقصور الثقافة',
                       'language': 'ara-arab'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '2014',
          'date': '2014'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
        'ara-arab': 'القاهرة : الهيئة العامة لقصور الثقافة, 2014',
        'default': 'al-Qāhirah : Al-Hayʾat al-ʿāmmah li quṣūr al-thaqāfah,' +
        ' 2014'
    }


def test_marc21_to_provisionActivity_2_places_2_agents_rus_cyrl():
    """Test dojson publication statement.
    - 2 places and 2 agents from one field 264
    - extract data from the linked 880 from 3 fields 880
    """
    marc21xml = """
      <record>
        <controlfield tag=
          "008">170626s2017    ru ||| |  ||||00|  |rus d</controlfield>
        <datafield tag="264" ind1=" " ind2="1">
          <subfield code="6">880-02</subfield>
          <subfield code="a">Ierusalim :</subfield>
          <subfield code="b">Gesharim ;</subfield>
          <subfield code="a">Moskva :</subfield>
          <subfield code="b">Mosty Kulʹtury,</subfield>
          <subfield code="c">2017</subfield>
        </datafield>
        <datafield tag="264" ind1=" " ind2="4">
          <subfield code="c">©2017</subfield>
        </datafield>
        <datafield tag="880" ind1=" " ind2="1">
          <subfield code="6">264-02/(N</subfield>
          <subfield code="a">Иерусалим :</subfield>
          <subfield code="b">Гешарим ;</subfield>
          <subfield code="a">Москва :</subfield>
          <subfield code="b">Мосты Культуры,</subfield>
          <subfield code="c">2017</subfield>
        </datafield>
        <datafield tag="880" ind1="1" ind2=" ">
          <subfield code="6">490-03/(N</subfield>
          <subfield code="a">Прошлый век. Воспоминания</subfield>
        </datafield>
        <datafield tag="880" ind1="1" ind2="0">
          <subfield code="6">245-01/(N</subfield>
          <subfield code="a">Воспоминания бабушки :</subfield>
          <subfield code=
              "b">очерки культурной истории евреев России в XIX в. /</subfield>
          <subfield code="c">Полина Венгерова</subfield>
        </datafield>
      </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('provisionActivity') == [
      {
          'type': 'bf:Publication',
          'statement': [
              {
                  'country': 'ru',
                  'label': [
                      {'value': 'Ierusalim'},
                      {'value': 'Иерусалим',
                       'language': 'rus-cyrl'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Gesharim'},
                      {'value': 'Гешарим',
                       'language': 'rus-cyrl'}
                  ],
                  'type': 'bf:Agent'
              },
              {
                  'label': [
                      {'value': 'Moskva'},
                      {'value': 'Москва',
                       'language': 'rus-cyrl'}
                  ],
                  'type': 'bf:Place'
              },
              {
                  'label': [
                      {'value': 'Mosty Kulʹtury'},
                      {'value': 'Мосты Культуры',
                       'language': 'rus-cyrl'}
                  ],
                  'type': 'bf:Agent'
              }
          ],
          'startDate': '2017',
          'date': '2017'
      }
    ]
    assert create_publication_statement(data.get('provisionActivity')[0]) == {
        'default': 'Ierusalim : Gesharim ; Moskva : Mosty Kulʹtury, 2017',
        'rus-cyrl': 'Иерусалим : Гешарим ; Москва : Мосты Культуры, 2017'
    }


# extent: 300$a (the first one if many)
# otherMaterialCharacteristics: 300$b (the first one if many)
# formats: 300 [$c repetitive]
def test_marc21_to_description():
    """Test dojson extent, otherMaterialCharacteristics, formats."""

    marc21xml = """
    <record>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">116 p.</subfield>
        <subfield code="b">ill.</subfield>
        <subfield code="c">22 cm</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('extent') == '116 p.'
    assert data.get('otherMaterialCharacteristics') == 'ill.'
    assert data.get('formats') == ['22 cm']

    marc21xml = """
    <record>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">116 p.</subfield>
        <subfield code="b">ill.</subfield>
        <subfield code="c">22 cm</subfield>
        <subfield code="c">12 x 15</subfield>
      </datafield>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">200 p.</subfield>
        <subfield code="b">ill.</subfield>
        <subfield code="c">19 cm</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('extent') == '116 p.'
    assert data.get('otherMaterialCharacteristics') == 'ill.'
    assert data.get('formats') == ['22 cm', '12 x 15']


# series.name: [490$a repetitive]
# series.number: [490$v repetitive]
def test_marc21_to_series():
    """Test dojson series."""

    marc21xml = """
    <record>
      <datafield tag="490" ind1=" " ind2=" ">
        <subfield code="a">Collection One</subfield>
        <subfield code="v">5</subfield>
      </datafield>
      <datafield tag="490" ind1=" " ind2=" ">
        <subfield code="a">Collection Two</subfield>
        <subfield code="v">123</subfield>
      </datafield>    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('series') == [
        {
            'name': 'Collection One',
            'number': '5'
        },
        {
            'name': 'Collection Two',
            'number': '123'
        }
    ]


# abstract: [520$a repetitive]
def test_marc21_to_abstract():
    """Test dojson abstract."""

    marc21xml = """
    <record>
      <datafield tag="520" ind1=" " ind2=" ">
        <subfield code="a">This book is about</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('abstracts') == ["This book is about"]


# notes: [500$a repetitive]
def test_marc21_to_notes():
    """Test dojson notes."""

    marc21xml = """
    <record>
      <datafield tag="500" ind1=" " ind2=" ">
        <subfield code="a">note 1</subfield>
      </datafield>
      <datafield tag="500" ind1=" " ind2=" ">
        <subfield code="a">note 2</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('notes') == ['note 1', 'note 2']


# is_part_of 773$t
def test_marc21_to_is_part_of():
    """Test dojson is_part_of."""

    marc21xml = """
    <record>
      <datafield tag="773" ind1="1" ind2=" ">
        <subfield code="t">Stuart Hall : critical dialogues</subfield>
        <subfield code="g">411</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('is_part_of') == 'Stuart Hall : critical dialogues'


# subjects: 6xx [duplicates could exist between several vocabularies,
# if possible deduplicate]
def test_marc21_to_subjects():
    """Test dojson subjects."""

    marc21xml = """
    <record>
      <datafield tag="600" ind1=" " ind2=" ">
        <subfield code="a">subjects 600</subfield>
      </datafield>
      <datafield tag="666" ind1=" " ind2=" ">
        <subfield code="a">subjects 666</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('subjects') == ['subjects 600', 'subjects 666']


def test_marc21_to_identifiedBy_from_020():
    """Test dojson identifiedBy from 020."""

    marc21xml = """
    <record>
      <datafield tag="020" ind1=" " ind2=" ">
        <subfield code="z">8124605254</subfield>
      </datafield>
      <datafield tag="020" ind1=" " ind2=" ">
        <subfield code="a">9788124605257 (broché)</subfield>
      </datafield>
      <datafield tag="020" ind1=" " ind2=" ">
        <subfield code="a">9788189997212</subfield>
        <subfield code="q">hbk.</subfield>
        <subfield code="c">£125.00</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Isbn',
            'status': 'invalid or cancelled',
            'value': '8124605254'
        },
        {
            'type': 'bf:Isbn',
            'qualifier': 'broché',
            'value': '9788124605257'
        },
        {
            'type': 'bf:Isbn',
            'qualifier': 'hbk.',
            'acquisitionsTerms': '£125.00',
            'value': '9788189997212'
        }
    ]


def test_marc21_to_identifiedBy_from_022():
    """Test dojson identifiedBy from 022."""

    marc21xml = """
    <record>
      <datafield tag="022" ind1=" " ind2=" ">
        <subfield code="a">0264-2875</subfield>
        <subfield code="l">0264-2875</subfield>
      </datafield>
      <datafield tag="022" ind1=" " ind2=" ">
        <subfield code="a">0264-2875</subfield>
        <subfield code="y">0080-4649</subfield>
      </datafield>
      <datafield tag="022" ind1=" " ind2=" ">
        <subfield code="m">0080-4650</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Issn',
            'value': '0264-2875'
        },
        {
            'type': 'bf:IssnL',
            'value': '0264-2875'
        },
        {
            'type': 'bf:Issn',
            'value': '0264-2875'
        },
        {
            'type': 'bf:Issn',
            'status': 'invalid',
            'value': '0080-4649'
        },
        {
            'type': 'bf:IssnL',
            'status': 'cancelled',
            'value': '0080-4650'
        }
    ]


def test_marc21_to_identifiedBy_from_024_snl_bnf():
    """Test dojson identifiedBy from 024 field snl and bnf."""
    marc21xml = """
    <record>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">http://permalink.snl.ch/bib/chccsa86779</subfield>
        <subfield code="2">permalink</subfield>
      </datafield>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">http://catalogue.bnf.fr/ark:/12148/cb312v</subfield>
        <subfield code="2">uri</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'uri',
            'source': 'SNL',
            'value': 'http://permalink.snl.ch/bib/chccsa86779'
        },
        {
            'type': 'uri',
            'source': 'BNF',
            'value': 'http://catalogue.bnf.fr/ark:/12148/cb312v'
        }
    ]


def test_marc21_to_identifiedBy_from_024_with_subfield_2():
    """Test dojson identifiedBy from 024 field with subfield 2."""

    marc21xml = """
    <record>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">10.1007/978-3-540-37973-7</subfield>
        <subfield code="c">£125.00</subfield>
        <subfield code="d">note</subfield>
        <subfield code="2">doi</subfield>
      </datafield>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">urn:nbn:de:101:1-201609052530</subfield>
        <subfield code="2">urn</subfield>
      </datafield>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">NIPO 035-16-060-7</subfield>
        <subfield code="2">nipo</subfield>
      </datafield>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">7290105422026</subfield>
        <subfield code="2">danacode</subfield>
      </datafield>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">VD18 10153438</subfield>
        <subfield code="2">vd18</subfield>
      </datafield>
      <datafield tag="024" ind1="7" ind2=" ">
        <subfield code="a">00028947969525</subfield>
        <subfield code="2">gtin-14</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Doi',
            'value': '10.1007/978-3-540-37973-7',
            'acquisitionsTerms': '£125.00',
            'note': 'note'
        },
        {
            'type': 'bf:Urn',
            'value': 'urn:nbn:de:101:1-201609052530'
        },
        {
            'type': 'bf:Local',
            'source': 'NIPO',
            'value': 'NIPO 035-16-060-7'
        },
        {
            'type': 'bf:Local',
            'source': 'danacode',
            'value': '7290105422026'
        },
        {
            'type': 'bf:Local',
            'source': 'vd18',
            'value': 'VD18 10153438'
        },
        {
            'type': 'bf:Gtin14Number',
            'value': '00028947969525'
        }
    ]


def test_marc21_to_identifiedBy_from_024_without_subfield_2():
    """Test dojson identifiedBy from 024 field without subfield 2."""

    marc21xml = """
    <record>
      <datafield tag="024" ind1=" " ind2=" ">
        <subfield code="a">9782100745463</subfield>
      </datafield>
      <datafield tag="024" ind1="0" ind2="1">
        <subfield code="a">702391010582 (vol. 2) </subfield>
      </datafield>
      <datafield tag="024" ind1="0" ind2="2">
        <subfield code="a">Erato ECD 88030</subfield>
      </datafield>
      <datafield tag="024" ind1="1" ind2=" ">
        <subfield code="a">604907014223 (vol. 5)</subfield>
      </datafield>
      <datafield tag="024" ind1="1" ind2="2">
        <subfield code="a">EMI Classics 5 55585 2</subfield>
      </datafield>
      <datafield tag="024" ind1="2" ind2=" ">
        <subfield code="a">M006546565 (kritischer B., kartoniert)</subfield>
        <subfield code="q">vol. 1</subfield>
      </datafield>
      <datafield tag="024" ind1="2" ind2=" ">
        <subfield code="a">9790201858135</subfield>
        <subfield code="q">Kritischer Bericht</subfield>
      </datafield>
      <datafield tag="024" ind1="2" ind2=" ">
        <subfield code="a">4018262101065 (Bd. 1)</subfield>
      </datafield>
      <datafield tag="024" ind1="3" ind2=" ">
        <subfield code="a">309-5-56-196162-1</subfield>
        <subfield code="q">CD audio classe</subfield>
      </datafield>
      <datafield tag="024" ind1="3" ind2=" ">
        <subfield code="a">9783737407427</subfield>
        <subfield code="q">Bd 1</subfield>
        <subfield code="q">pbk.</subfield>
      </datafield>
      <datafield tag="024" ind1="3" ind2="2">
        <subfield code="a">EP 2305</subfield>
      </datafield>
      <datafield tag="024" ind1="3" ind2="2">
        <subfield code="a">97 EP 1234</subfield>
      </datafield>
     <datafield tag="024" ind1="8" ind2=" ">
        <subfield code="a">ELC1283925</subfield>
      </datafield>
      <datafield tag="024" ind1="8" ind2=" ">
        <subfield code="a">0000-0002-A3B1-0000-0-0000-0000-2</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Identifier',
            'value': '9782100745463'
        },
        {
            'type': 'bf:Isrc',
            'qualifier': 'vol. 2',
            'value': '702391010582'
        },
        {
            'type': 'bf:Isrc',
            'value': 'Erato ECD 88030'
        },
        {
            'type': 'bf:Upc',
            'qualifier': 'vol. 5',
            'value': '604907014223'
        },
        {
            'type': 'bf:Upc',
            'value': 'EMI Classics 5 55585 2'
        },
        {
            'type': 'bf:Ismn',
            'qualifier': 'kritischer B., kartoniert, vol. 1',
            'value': 'M006546565'
        },
        {
            'type': 'bf:Ismn',
            'qualifier': 'Kritischer Bericht',
            'value': '9790201858135'
        },
        {
            'type': 'bf:Identifier',
            'qualifier': 'Bd. 1',
            'value': '4018262101065'
        },
        {
            'type': 'bf:Identifier',
            'qualifier': 'CD audio classe',
            'value': '309-5-56-196162-1'
        },
        {
            'type': 'bf:Ean',
            'qualifier': 'Bd 1, pbk.',
            'value': '9783737407427'
        },
        {
            'type': 'bf:Identifier',
            'value': 'EP 2305'
        },
        {
            'type': 'bf:Ean',
            'value': '97 EP 1234'
        },
        {
            'type': 'bf:Identifier',
            'value': 'ELC1283925'
        },
        {
            'type': 'bf:Isan',
            'value': '0000-0002-A3B1-0000-0-0000-0000-2'
        }
    ]


def test_marc21_to_identifiedBy_from_028():
    """Test dojson identifiedBy from 035."""

    marc21xml = """
    <record>
      <datafield tag="028" ind1="3" ind2=" ">
        <subfield code="a">1234</subfield>
        <subfield code="b">SRC</subfield>
        <subfield code="q">Qualif1</subfield>
        <subfield code="q">Qualif2</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:MusicPublisherNumber',
            'source': 'SRC',
            'qualifier': 'Qualif1, Qualif2',
            'value': '1234'
        }
    ]

    marc21xml = """
    <record>
      <datafield tag="028" ind1="9" ind2=" ">
        <subfield code="a">1234</subfield>
        <subfield code="b">SRC</subfield>
        <subfield code="q">Qualif1</subfield>
        <subfield code="q">Qualif2</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Identifier',
            'source': 'SRC',
            'qualifier': 'Qualif1, Qualif2',
            'value': '1234'
        }
    ]


def test_marc21_to_identifiedBy_from_035():
    """Test dojson identifiedBy from 035."""

    marc21xml = """
    <record>
      <datafield tag="035" ind1=" " ind2=" ">
        <subfield code="a">R008945501</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Local',
            'source': 'RERO',
            'value': 'R008945501'
        }
    ]


def test_marc21_to_identifiedBy_from_930():
    """Test dojson identifiedBy from 930."""

    # identifier with source in parenthesis
    marc21xml = """
    <record>
      <datafield tag="930" ind1=" " ind2=" ">
        <subfield code="a">(OCoLC) ocm11113722</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Local',
            'source': 'OCoLC',
            'value': 'ocm11113722'
        }
    ]
    # identifier without source in parenthesis
    marc21xml = """
    <record>
      <datafield tag="930" ind1=" " ind2=" ">
        <subfield code="a">ocm11113722</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('identifiedBy') == [
        {
            'type': 'bf:Local',
            'value': 'ocm11113722'
        }
    ]


@mock.patch('requests.get')
def test_get_mef_person_link(mock_get, capsys):
    """Test get mef person link"""
    mock_get.return_value = mock_response(json_data={
        'hits': {
            'hits': [{'links': {'self': 'mocked_url'}}]
        }
    })
    mef_url = get_mef_person_link(
        id='(RERO)A003945843',
        key='100..',
        value={'0': '(RERO)A003945843'}
    )
    assert mef_url == 'mocked_url'

    os.environ['RERO_ILS_MEF_HOST'] = 'mefdev.test.rero.ch'
    mef_url = get_mef_person_link(
        id='(RERO)A003945843',
        key='100..',
        value={'0': '(RERO)A003945843'}
    )
    assert mef_url == 'mocked_url'

    mock_get.return_value = mock_response(status=400)
    mef_url = get_mef_person_link(
        id='(RERO)AXXXXXXXXX',
        key='100..',
        value={'0': '(RERO)AAXXXXXXXXX'}
    )
    assert not mef_url
    out, err = capsys.readouterr()
    assert err == 'ERROR: MEF request ' +\
        'https://mefdev.test.rero.ch/api/mef/?q=rero.pid:AXXXXXXXXX 400\n'
