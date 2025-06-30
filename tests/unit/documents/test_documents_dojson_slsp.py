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


def test_marc21_to_contribution():
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
    assert data.get("contribution") == [
        {
            "entity": {
                "type": "bf:Person",
                "authorized_access_point": "Jean-Paul II, Pape, 1954",
            },
            "role": ["aut"],
        },
        {
            "entity": {
                "type": "bf:Person",
                "authorized_access_point": "Dumont, Jean, 1921-2014, Historien",
            },
            "role": ["edt"],
        },
        {
            "entity": {"type": "bf:Organisation", "authorized_access_point": "RERO"},
            "role": ["ctb"],
        },
        {
            "entity": {
                "type": "bf:Organisation",
                "authorized_access_point": "Biennale de céramique contemporaine (17 : 2003 : Châteauroux)",
            },
            "role": ["aut"],
        },
    ]
    assert data.get("work_access_point") == [
        {
            "creator": {
                "date_of_birth": "1954",
                "numeration": "II",
                "preferred_name": "Jean-Paul",
                "qualifier": "Pape",
                "type": "bf:Person",
            },
            "title": "Treaties, etc.",
        },
        {
            "creator": {"preferred_name": "Santamaría, Germán", "type": "bf:Person"},
            "language": "fre",
            "title": "No morirás",
        },
        {
            "miscellaneous_information": "language: Coréen",
            "part": [{"partName": "A.T. et N.T.", "partNumber": "000"}],
            "title": "Bible",
        },
    ]

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
    assert data.get("work_access_point") == [
        {
            "creator": {
                "date_of_birth": "1919",
                "date_of_death": "1990",
                "preferred_name": "Santamaría, Germán",
                "type": "bf:Person",
            },
            "title": "No morirás",
        },
        {
            "creator": {
                "date_of_birth": "1919",
                "preferred_name": "Santamaría, Germán",
                "type": "bf:Person",
            },
            "title": "No morirás",
        },
    ]


@mock.patch(
    "rero_ils.modules.documents.dojson.contrib.marc21tojson.slsp.model.get_mef_link"
)
def test_marc21_to_subjects(mock_get_mef_link):
    """Test dojson subjects imported from 6xx."""

    # 600 Person => to import (all subfields)
    marc21xml = """
    <record>
      <datafield tag="600" ind1="2" ind2="0">
        <subfield code="a">Person</subfield>
      </datafield>
      <datafield tag="600" ind1="2" ind2="0">
        <subfield code="a">Person MEF</subfield>
        <subfield code="0">(DE-588)TEST)</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://test.rero.ch/api/agents/gnd/PERSON"
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Person",
                "authorized_access_point": "Person",
                "source": "LCSH",
            }
        }
    ]
    assert data.get("subjects") == [
        {"entity": {"$ref": "https://test.rero.ch/api/agents/gnd/PERSON"}}
    ]

    # 610 Organisation => to import (all subfields)
    marc21xml = """
    <record>
      <datafield tag="610" ind1="2" ind2="0">
        <subfield code="a">Organisation</subfield>
      </datafield>
      <datafield tag="610" ind1="2" ind2="0">
        <subfield code="a">Organisation</subfield>
        <subfield code="0">(DE-588)TEST)</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://test.rero.ch/api/agents/gnd/ORGANISATION"
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Organisation",
                "authorized_access_point": "Organisation",
                "source": "LCSH",
            }
        }
    ]
    assert data.get("subjects") == [
        {"entity": {"$ref": "https://test.rero.ch/api/agents/gnd/ORGANISATION"}}
    ]

    # 611 Congresses and events => import (all subfields) into which field? Congress does not exist...
    #  611 0x et 611 1x =>organisation;
    #  611 2x => organisation + convention specification as entry under convention name
    marc21xml = """
    <record>
      <datafield tag="611" ind1="0" ind2="0">
        <subfield code="a">Organisation</subfield>
      </datafield>
      <datafield tag="611" ind1="2" ind2="0">
        <subfield code="a">Convention</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Organisation",
                "authorized_access_point": "Organisation",
                "source": "LCSH",
            }
        },
        {
            "entity": {
                "type": "bf:Organisation",
                "authorized_access_point": "Convention",
                "source": "LCSH",
            },
        },
    ]

    # 630 Uniform titles => import (all subfields) into Oeuvre
    marc21xml = """
    <record>
      <datafield tag="630" ind1="0" ind2="0">
        <subfield code="a">Uniform Title</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Work",
                "authorized_access_point": "Uniform Title",
                "source": "LCSH",
            }
        }
    ]

    # 647 Event (hurricane, earthquake, financial crisis, war, volcanic eruption...)
    #  (in IdRef these are currently 650) => import (all subfields) into
    #  Theme (risk of changes following modifications to RDA rules)
    marc21xml = """
    <record>
      <datafield tag="647" ind1="0" ind2="0">
        <subfield code="a">Earthquake</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    # TODO: implement transformation
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") is None

    # 648 Chronological term (1863) (1900-1999) => import (all sub-fields) in Time frame
    marc21xml = """
    <record>
      <datafield tag="648" ind1="0" ind2="0">
        <subfield code="a">1900-1999</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    # TODO: implement transformation
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "authorized_access_point": "1900-1999",
                "source": "LCSH",
                "type": "bf:Temporal",
            }
        }
    ]

    # 650 Common name => import (all subfields) into Theme

    # 651 Geographic name => import (all subfields) in Places
    # 651	_	7	$a Schweizer Mittelland $z West $0 (DE-588)4386654-2 $2 gnd
    marc21xml = """
    <record>
      <datafield tag="651" ind1="0" ind2="0">
        <subfield code="a">Schweizer Mittelland</subfield>
        <subfield code="z">West</subfield>
      </datafield>
      <datafield tag="651" ind1="0" ind2="0">
        <subfield code="a">Schweizer Mittelland</subfield>
        <subfield code="z">West</subfield>
        <subfield code="0">(DE-588)4386654-2</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://test.rero.ch/api/places/gnd/PLACE"
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Place",
                "authorized_access_point": "Schweizer Mittelland",
                "subdivisions": [
                    {"entity": {"authorized_access_point": "West", "type": "bf:Place"}}
                ],
                "source": "LCSH",
            }
        }
    ]
    assert data.get("subjects") == [
        {"entity": {"$ref": "https://test.rero.ch/api/places/gnd/PLACE"}}
    ]

    # 655 Genre or form => import (all subfields) in Genre, form
    # 655	_	7	$a Bildband $2 gnd-content
    # 655	_	7	$a Photographie $0 (IDREF)028224248 $2 idref
    marc21xml = """
    <record>
      <datafield tag="655" ind1="0" ind2="0">
        <subfield code="a">Bildband</subfield>
        <subfield code="2">gnd-content</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("genreForm") == [
        {
            "entity": {"type": "bf:Topic", "authorized_access_point": "Bildband"},
        },
    ]
    marc21xml = """
    <record>
      <datafield tag="655" ind1="0" ind2="0">
        <subfield code="a">Photographie</subfield>
        <subfield code="0">(IDREF)028224248</subfield>
        <subfield code="2">idref</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://test.rero.ch/api/concepts/TOPIC"
    data = marc21.do(marc21json)
    assert data.get("genreForm") == [
        {"entity": {"$ref": "https://test.rero.ch/api/concepts/TOPIC"}},
    ]
