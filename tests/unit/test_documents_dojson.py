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

"""DOJSON module tests."""

from __future__ import absolute_import, print_function

from dojson.contrib.marc21.utils import create_record

from rero_ils.modules.documents.dojson.contrib.marc21tojson import marc21tojson


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
        <subfield code="a">eng</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('language') == [
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


# publishers.name: 264 [$b repetitive] (without the , but keep the ;)
# publishers.place: 264 [$a repetitive] (without the : but keep the ;)
# publicationDate: 264 [$c repetitive] (but take only the first one)
def test_marc21_to_publishers_publicationDate():
    """Test dojson publishers publicationDate."""

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2=" ">
        <subfield code="a">Lausanne :</subfield>
        <subfield code="b">Payot,</subfield>
        <subfield code="c">2015</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('publishers') == [
        {
            'place': ['Lausanne'],
            'name': ['Payot'],
        }
    ]
    assert data.get('publicationYear') == 2015

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2=" ">
        <subfield code="a">Lausanne :</subfield>
        <subfield code="b">Payot,</subfield>
        <subfield code="c">2015</subfield>
      </datafield>
      <datafield tag="260" ind1=" " ind2=" ">
        <subfield code="c">2016</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('publishers') == [
        {
            'place': ['Lausanne'],
            'name': ['Payot'],
        }
    ]
    assert data.get('publicationYear') == 2015

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2=" ">
        <subfield code="a">Paris ;</subfield>
        <subfield code="a">Lausanne :</subfield>
        <subfield code="b">Payot,</subfield>
        <subfield code="c">1920</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('publishers') == [
        {
            'place': ['Paris', 'Lausanne'],
            'name': ['Payot'],
        }
    ]
    assert data.get('publicationYear') == 1920

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2=" ">
        <subfield code="a">Paris :</subfield>
        <subfield code="b">Champion ;</subfield>
        <subfield code="a">Genève :</subfield>
        <subfield code="b">Droz,</subfield>
        <subfield code="c">1912-1955</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert data.get('publishers') == [
        {
            'place': ['Paris'],
            'name': ['Champion']
        },
        {
            'place': ['Genève'],
            'name': ['Droz']
        }
    ]
    assert data.get('freeFormedPublicationDate') == '1912-1955'
    assert data.get('publicationYear') == 1912

    marc21xml = """
    <record>
      <datafield tag="264" ind1=" " ind2="1">
        <subfield code="c">1984</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21tojson.do(marc21json)
    assert 'publishers' not in data
    assert data.get('publicationYear') == 1984


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
