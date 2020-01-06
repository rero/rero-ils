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

from dojson.contrib.marc21.utils import create_record

from rero_ils.modules.documents.dojson.contrib.unimarctojson import \
    unimarctojson


# type: leader
def test_unimarc_to_type():
    """
    Test dojson unimarc_to_type.

    Books: LDR/6-7: am
    Journals: LDR/6-7: as
    Articles: LDR/6-7: aa + add field 773 (journal title)
    Scores: LDR/6: c|d
    Videos: LDR/6: g + 007/0: m|v
    Sounds: LDR/6: i|j
    E-books (imported from Cantook)
    """

    unimarcxml = """
    <record>
        <leader>00501nam a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'book'

    unimarcxml = """
    <record>
        <leader>00501nas a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'journal'

    unimarcxml = """
    <record>
        <leader>00501naa a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'article'

    unimarcxml = """
    <record>
        <leader>00501nca a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'score'
    unimarcxml = """
    <record>
        <leader>00501nda a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'score'

    unimarcxml = """
    <record>
        <leader>00501nia a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'sound'
    unimarcxml = """
    <record>
        <leader>00501nja a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'sound'

    unimarcxml = """
    <record>
        <leader>00501nga a2200133 a 4500</leader>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('type') == 'video'


# title: 200$a
# without the punctuaction. If there's a $e, then 200$a : $e
def test_unimarctotitle():
    """Test dojson unimarctotitle."""

    # subfields $a $b $c
    unimarcxml = """
    <record>
      <datafield tag="200" ind1="1" ind2="0">
        <subfield code="a">main title</subfield>
        <subfield code="e">subtitle</subfield>
        <subfield code="f">responsibility</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('title') == 'main title : subtitle'
    # subfields $a $c
    unimarcxml = """
    <record>
      <datafield tag="200" ind1="1" ind2="0">
        <subfield code="a">main title</subfield>
        <subfield code="f">responsibility</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('title') == 'main title'
    # subfield $a
    unimarcxml = """
    <record>
      <datafield tag="200" ind1="1" ind2="0">
        <subfield code="a">main title</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('title') == 'main title'


# titleProper: [500$a repetitive]
def test_unimarctotitlesProper():
    """Test dojson unimarc_titlesProper."""

    unimarcxml = """
    <record>
      <datafield tag="500" ind1="1" ind2="0">
        <subfield code="a">proper title</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('titlesProper') == ['proper title']

    unimarcxml = """
    <record>
      <datafield tag="500" ind1=" " ind2=" ">
        <subfield code="a">proper title</subfield>
      </datafield>
      <datafield tag="500" ind1=" " ind2=" ">
         <subfield code="a">other proper title</subfield>
       </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('titlesProper') == ['proper title', 'other proper title']


# languages: 101 [$a]
def test_unimarc_languages():
    """Test dojson unimarc_languages."""

    unimarcxml = """
    <record>
      <datafield tag="101" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('language') == [{'value': 'eng', 'type': 'bf:Language'}]

    unimarcxml = """
    <record>
      <datafield tag="101" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        <subfield code="a">fre</subfield>
        <subfield code="c">ita</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('language') == [
        {'value': 'eng', 'type': 'bf:Language'},
        {'value': 'fre', 'type': 'bf:Language'}
    ]
    assert data.get('translatedFrom') == ['ita']

    unimarcxml = """
    <record>
      <datafield tag="101" ind1=" " ind2=" ">
        <subfield code="a">eng</subfield>
        <subfield code="a">???</subfield>
        <subfield code="c">ita</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('language') == [
        {'value': 'eng', 'type': 'bf:Language'},
    ]
    assert data.get('translatedFrom') == ['ita']


# authors: loop:
# 700 Nom de personne – Responsabilité principale
# 701 Nom de personne – Autre responsabilité principale
# 702 Nom de personne – Responsabilité secondaire
# 710 Nom de collectivité – Responsabilité principale
# 711 Nom de collectivité – Autre responsabilité principale
# 712 Nom de collectivité – Responsabilité secondaire
def test_unimarctoauthors():
    """Test dojson unimarctoauthors."""

    unimarcxml = """
    <record>
      <datafield tag="700" ind1=" " ind2=" ">
        <subfield code="a">Jean-Paul</subfield>
        <subfield code="d">II</subfield>
        <subfield code="c">Pape</subfield>
        <subfield code="f">1954 -</subfield>
      </datafield>
      <datafield tag="701" ind1=" " ind2=" ">
        <subfield code="a">Dumont</subfield>
        <subfield code="b">Jean</subfield>
        <subfield code="c">Historien</subfield>
        <subfield code="f">1921 - 2014</subfield>
      </datafield>
      <datafield tag="702" ind1=" " ind2=" ">
        <subfield code="a">Dicker</subfield>
        <subfield code="b">J.</subfield>
        <subfield code="f">1921 -</subfield>
      </datafield>
      <datafield tag="710" ind1=" " ind2=" ">
        <subfield code="a">RERO</subfield>
      </datafield>
      <datafield tag="711" ind1=" " ind2=" ">
        <subfield code="a">LOC</subfield>
      </datafield>
      <datafield tag="712" ind1=" " ind2=" ">
        <subfield code="a">BNF</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    authors = data.get('authors')
    assert authors == [
        {
            'name': 'Jean-Paul II',
            'type': 'person',
            'date': '1954 -',
            'qualifier': 'Pape'
        },
        {
            'name': 'Dumont, Jean',
            'type': 'person',
            'date': '1921 - 2014',
            'qualifier': 'Historien'
        },
        {
            'name': 'Dicker, J.',
            'type': 'person',
            'date': '1921 -'
        },
        {
            'name': 'RERO',
            'type': 'organisation'
        },
        {
            'name': 'LOC',
            'type': 'organisation'
        },
        {
            'name': 'BNF',
            'type': 'organisation'
        }
    ]


def test_unimarc_edition():
    """Test dojson edition statement.
    - 1 edition designation and 1 responsibility from field 205
    """
    unimarcxml = """
    <record>
      <datafield tag="205" ind1=" " ind2=" ">
        <subfield code="a">2e ed.</subfield>
        <subfield code="f">avec un avant-propos par Jean Faret</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('editionStatement') == [
      {
        'editionDesignation': [
          {
            'value': '2e ed.'
          }
        ],
        'responsibility': [
          {
            'value': 'avec un avant-propos par Jean Faret'
          }
        ]
      }
    ]


def test_unimarc_publishers_provision_activity():
    """Test dojson publishers publicationDate."""

    unimarcxml = """
    <record>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">xxxxxxxxx2015????xxxxxxxxx</subfield>
      </datafield>
      <datafield tag="210" ind1=" " ind2=" ">
        <subfield code="a">Lausanne</subfield>
        <subfield code="c">Payot</subfield>
        <subfield code="d">2015</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Publication',
        'statement': [
            {
                'label': [
                    {'value': 'Lausanne'}
                ],
                'type': 'bf:Place'
            },
            {
                'label': [
                    {'value': 'Payot'}
                ],
                'type': 'bf:Agent'
            },
            {
                'label': [
                    {'value': '2015'}
                ],
                'type': 'Date'
            }
        ],
        'startDate': '2015',
    }]

    unimarcxml = """
    <record>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">xxxxxxxxx2015????xxxxxxxxx</subfield>
      </datafield>
      <datafield tag="210" ind1=" " ind2=" ">
        <subfield code="a">Lausanne</subfield>
        <subfield code="c">Payot</subfield>
        <subfield code="d">2015</subfield>
      </datafield>
      <datafield tag="210" ind1=" " ind2=" ">
        <subfield code="e">Lausanne</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Publication',
        'statement': [
            {
                'label': [
                    {'value': 'Lausanne'}
                ],
                'type': 'bf:Place'
            },
            {
                'label': [
                    {'value': 'Payot'}
                ],
                'type': 'bf:Agent'
            },
            {
                'label': [
                    {'value': '2015'}
                ],
                'type': 'Date'
            }
        ],
        'startDate': '2015',
    }]

    unimarcxml = """
    <record>
      <datafield tag="102" ind1=" " ind2=" ">
        <subfield code="a">FR</subfield>
      </datafield>
      <datafield tag="210" ind1=" " ind2=" ">
        <subfield code="a">[Paris] :</subfield>
        <subfield code="c">Desclée de Brouwer [puis] </subfield>
        <subfield code="c">Etudes augustiniennes,</subfield>
        <subfield code="d">[1969-1999]</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Publication',
        'place': [
            {
                'country': 'fr',
                'type': 'bf:Place'
            },
        ],
        'statement': [
            {
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
            },
            {
                'label': [
                    {'value': '[1969-1999]'}
                ],
                'type': 'Date'
            }
        ],
        'startDate': '1969',
        'endDate': '1999',
    }]

    unimarcxml = """
    <record>
      <datafield tag="214" ind1=" " ind2="0">
        <subfield code="a">Paris</subfield>
        <subfield code="c">Champion</subfield>
        <subfield code="a">Genève</subfield>
        <subfield code="c">Droz</subfield>
        <subfield code="d">1912-1955</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Publication',
        'statement': [
            {
                'label': [
                    {'value': 'Paris'}
                ],
                'type': 'bf:Place'
            },
            {
                'label': [
                    {'value': 'Champion'}
                ],
                'type': 'bf:Agent'
            },
            {
                'label': [
                    {'value': 'Genève'}
                ],
                'type': 'bf:Place'
            },
            {
                'label': [
                    {'value': 'Droz'}
                ],
                'type': 'bf:Agent'
            },
            {
                'label': [
                    {'value': '1912-1955'}
                ],
                'type': 'Date'
            }
        ],
        'startDate': '1912',
        'endDate': '1955'
    }]

    unimarcxml = """
    <record>
      <datafield tag="214" ind1=" " ind2="1">
        <subfield code="a">Lausanne</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Production',
        'statement': [
            {
                'label': [
                    {'value': 'Lausanne'}
                ],
                'type': 'bf:Place'
            }
        ],
    }]

    unimarcxml = """
    <record>
      <datafield tag="214" ind1=" " ind2="2">
        <subfield code="a">Lausanne</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Distribution',
        'statement': [
            {
                'label': [
                    {'value': 'Lausanne'}
                ],
                'type': 'bf:Place'
            }
        ],
    }]

    unimarcxml = """
    <record>
      <datafield tag="214" ind1=" " ind2="3">
        <subfield code="a">Lausanne</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('provisionActivity') == [{
        'type': 'bf:Manufacture',
        'statement': [
            {
                'label': [
                    {'value': 'Lausanne'}
                ],
                'type': 'bf:Place'
            }
        ],
    }]


def test_unimarc_copyright_date():
    """Test copyright date."""
    unimarcxml = """
    <record>
      <datafield tag="214" ind1=" " ind2="4">
        <subfield code="d">1919</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('copyrightDate') == ['© 1919']

    unimarcxml = """
    <record>
      <datafield tag="214" ind1=" " ind2="4">
        <subfield code="d">P 1919</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('copyrightDate') == ['℗ 1919']


# extent: 215$a (the first one if many)
# otherMaterialCharacteristics: 215$c (the first one if many)
# formats: 215 [$d repetitive]
def test_unimarc_description():
    """Test dojson extent, otherMaterialCharacteristics, formats."""

    unimarcxml = """
    <record>
      <datafield tag="215" ind1=" " ind2=" ">
        <subfield code="a">116 p.</subfield>
        <subfield code="c">ill.</subfield>
        <subfield code="d">22 cm</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('extent') == '116 p.'
    assert data.get('otherMaterialCharacteristics') == 'ill.'
    assert data.get('formats') == ['22 cm']

    unimarcxml = """
    <record>
      <datafield tag="215" ind1=" " ind2=" ">
        <subfield code="a">116 p.</subfield>
        <subfield code="c">ill.</subfield>
        <subfield code="d">22 cm</subfield>
        <subfield code="d">12 x 15</subfield>
      </datafield>
      <datafield tag="215" ind1=" " ind2=" ">
        <subfield code="a">200 p.</subfield>
        <subfield code="c">ill.</subfield>
        <subfield code="d">19 cm</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('extent') == '116 p.'
    assert data.get('otherMaterialCharacteristics') == 'ill.'
    assert data.get('formats') == ['22 cm', '12 x 15']


# series.name: [225$a repetitive]
# series.number: [225$v repetitive]
def test_unimarc_series():
    """Test dojson series."""

    unimarcxml = """
    <record>
      <datafield tag="225" ind1=" " ind2=" ">
        <subfield code="a">Collection One</subfield>
        <subfield code="v">5</subfield>
      </datafield>
      <datafield tag="225" ind1=" " ind2=" ">
        <subfield code="a">Collection Two</subfield>
        <subfield code="v">123</subfield>
      </datafield>    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
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


# abstract: [330$a repetitive]
def test_unimarc_abstract():
    """Test dojson abstract."""

    unimarcxml = """
    <record>
      <datafield tag="330" ind1=" " ind2=" ">
        <subfield code="a">This book is about</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('abstracts') == ["This book is about"]


# identifiers:isbn: 010$a
def test_unimarc_identifiers():
    """Test dojson identifiers."""

    unimarcxml = """
    <record>
      <controlfield
        tag="003">http://catalogue.bnf.fr/ark:/12148/cb350330441</controlfield>
      <datafield tag="073" ind1=" " ind2=" ">
        <subfield code="a">9782370550163</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('identifiedBy') == [
      {
        "type": "bf:Local",
        "value": "ark:/12148/cb350330441",
        "source": "BNF"
      },
      {
        "type": "bf:Ean",
        "value": "9782370550163"
      }
    ]

    unimarcxml = """
    <record>
      <datafield tag="073" ind1=" " ind2=" ">
        <subfield code="a">978237055016x</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('identifiedBy') == [
      {
        "type": "bf:Ean",
        "value": "978237055016x",
        "status": "invalid"
      }
    ]


# notes: [300$a repetitive]
def test_unimarc_notes():
    """Test dojson notes."""

    unimarcxml = """
    <record>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">note</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('notes') == ['note']
    unimarcxml = """
    <record>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">note 1</subfield>
      </datafield>
      <datafield tag="300" ind1=" " ind2=" ">
        <subfield code="a">note 2</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('notes') == ['note 1', 'note 2']


# subjects: 600..617 $a,$b,$c,$d,$f
# [duplicates could exist between several vocabularies,
# if possible deduplicate]
def test_unimarc_subjects():
    """Test dojson subjects."""

    unimarcxml = """
    <record>
      <datafield tag="600" ind1=" " ind2=" ">
        <subfield code="a">subjects 600</subfield>
      </datafield>
      <datafield tag="616" ind1=" " ind2=" ">
        <subfield code="a">Capet</subfield>
        <subfield code="b">Louis</subfield>
        <subfield code="c">Jr.</subfield>
        <subfield code="d">III</subfield>
        <subfield code="f">1700-1780</subfield>
      </datafield>
    </record>
    """
    unimarcjson = create_record(unimarcxml)
    data = unimarctojson.do(unimarcjson)
    assert data.get('subjects') == [
        'subjects 600', 'Capet, Louis III, Jr., 1700-1780'
    ]
