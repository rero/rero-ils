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

"""DOJSON LOC model tests."""

from unittest import mock

from dojson.contrib.marc21.utils import create_record

from rero_ils.modules.documents.dojson.contrib.marc21tojson.loc import marc21


@mock.patch("rero_ils.modules.documents.dojson.contrib.marc21tojson.loc.model.get_mef_link")
def test_marc21_to_subjects_gnd_routing(mock_get_mef_link):
    """Test that GND subjects always go to subjects field, not subjects_imported."""

    # Test 1: GND subject WITHOUT MEF link should go to subjects
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Computer science</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Computer science",
            }
        }
    ]
    assert data.get("subjects_imported") is None

    # Test 2: GND subject WITH MEF link should go to subjects
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Mathematics</subfield>
        <subfield code="0">(DE-588)123456789</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://test.rero.ch/api/concepts/gnd/123456789"
    data = marc21.do(marc21json)
    assert data.get("subjects") == [{"entity": {"$ref": "https://test.rero.ch/api/concepts/gnd/123456789"}}]
    assert data.get("subjects_imported") is None

    # Test 3: RERO subject should go to subjects_imported
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Physics</subfield>
        <subfield code="2">rero</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Physics",
            }
        }
    ]
    assert data.get("subjects") is None

    # Test 4: IDREF subject should go to subjects_imported
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Chemistry</subfield>
        <subfield code="2">idref</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Chemistry",
            }
        }
    ]
    assert data.get("subjects") is None

    # Test 5: LCSH subject (indicator 2=0) should go to subjects_imported
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="0">
        <subfield code="a">Astronomy</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Astronomy",
                "source": "LCSH",
            }
        }
    ]
    assert data.get("subjects") is None

    # Test 6: MeSH subject (indicator 2=2) should go to subjects_imported
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="2">
        <subfield code="a">Neurology</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Neurology",
                "source": "MeSH",
            }
        }
    ]
    assert data.get("subjects") is None

    # Test 7: Mixed GND and non-GND subjects should be routed correctly
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Biology</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Geology</subfield>
        <subfield code="2">rero</subfield>
      </datafield>
      <datafield tag="650" ind1=" " ind2="0">
        <subfield code="a">Ecology</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Biology",
            }
        }
    ]
    assert data.get("subjects_imported") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Geology",
            }
        },
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Ecology",
                "source": "LCSH",
            }
        },
    ]

    # Test 8: gnd-content should be treated as gnd and go to subjects
    marc21xml = """
    <record>
      <datafield tag="655" ind1=" " ind2="7">
        <subfield code="a">Documentary</subfield>
        <subfield code="2">gnd-content</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("genreForm") == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Documentary",
            }
        }
    ]

    # Test 9: GND Person subject WITHOUT MEF link
    marc21xml = """
    <record>
      <datafield tag="600" ind1=" " ind2="7">
        <subfield code="a">Einstein, Albert</subfield>
        <subfield code="d">1879-1955</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data.get("subjects") == [
        {
            "entity": {
                "type": "bf:Person",
                "authorized_access_point": "Einstein, Albert 1879-1955",
            }
        }
    ]
    assert data.get("subjects_imported") is None

    # Test 10: GND Place subject WITH MEF link
    marc21xml = """
    <record>
      <datafield tag="651" ind1=" " ind2="7">
        <subfield code="a">Berlin</subfield>
        <subfield code="0">(DE-588)4005728-8</subfield>
        <subfield code="2">gnd</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://test.rero.ch/api/places/gnd/4005728-8"
    data = marc21.do(marc21json)
    assert data.get("subjects") == [{"entity": {"$ref": "https://test.rero.ch/api/places/gnd/4005728-8"}}]
    assert data.get("subjects_imported") is None
