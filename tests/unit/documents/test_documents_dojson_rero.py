# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""DOJSON RERO model tests."""

from unittest import mock

import pytest
from dojson.contrib.marc21.utils import create_record

from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21
from rero_ils.modules.documents.models import DocumentFictionType


@pytest.mark.parametrize(
    "char,expected",
    [
        ("1", DocumentFictionType.Fiction.value),
        ("d", DocumentFictionType.Fiction.value),
        ("f", DocumentFictionType.Fiction.value),
        ("j", DocumentFictionType.Fiction.value),
        ("p", DocumentFictionType.Fiction.value),
        ("0", DocumentFictionType.NonFiction.value),
        ("e", DocumentFictionType.NonFiction.value),
        ("h", DocumentFictionType.NonFiction.value),
        ("i", DocumentFictionType.NonFiction.value),
        ("s", DocumentFictionType.NonFiction.value),
        (" ", DocumentFictionType.Unspecified.value),
    ],
)
def test_marc21_to_fiction_statement(char, expected):
    """Test fiction_statement extraction from 008 position 33."""
    marc21xml = f"""
    <record>
      <controlfield tag="008">160315s2015    cc ||| |  ||||00| {char}|chi d</controlfield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data["fiction_statement"] == expected


@pytest.mark.parametrize("genre_form_value", ["Fictions", "Films de fiction"])
@mock.patch("rero_ils.modules.documents.dojson.contrib.marc21tojson.rero.model.get_mef_link")
def test_marc21_to_fiction_statement_from_genreform(mock_get_mef_link, genre_form_value):
    """Test that fiction genreForm terms set fiction_statement to Fiction."""
    marc21xml = f"""
    <record>
      <datafield tag="655" ind1="0" ind2="7">
        <subfield code="a">{genre_form_value}</subfield>
        <subfield code="2">rero</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data["fiction_statement"] == DocumentFictionType.Fiction.value


@mock.patch("rero_ils.modules.documents.dojson.contrib.marc21tojson.rero.model.get_mef_link")
def test_marc21_to_fiction_statement_genreform_overrides_008(mock_get_mef_link):
    """Test that 'Fictions' genreForm overrides NonFiction value derived from 008."""
    marc21xml = """
    <record>
      <controlfield tag="008">160315s2015    cc ||| |  ||||00| 0|chi d</controlfield>
      <datafield tag="655" ind1="0" ind2="7">
        <subfield code="a">Fictions</subfield>
        <subfield code="2">rero</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = None
    data = marc21.do(marc21json)
    assert data["fiction_statement"] == DocumentFictionType.Fiction.value


@mock.patch("rero_ils.modules.documents.dojson.contrib.marc21tojson.rero.model.get_mef_link")
def test_marc21_to_subjects_rero_vocabulary(mock_get_mef_link):
    """Test that 650 $2 rero subjects go to subjects, not subjects_imported."""
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Informatique</subfield>
        <subfield code="2">rero</subfield>
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
                "source": "rero",
                "authorized_access_point": "Informatique",
            }
        }
    ]
    assert data.get("subjects_imported") is None


@mock.patch("rero_ils.modules.documents.dojson.contrib.marc21tojson.rero.model.get_mef_link")
def test_marc21_to_subjects_rero_vocabulary_with_mef_link(mock_get_mef_link):
    """Test that 650 $2 rero with a MEF link resolves to a $ref in subjects."""
    marc21xml = """
    <record>
      <datafield tag="650" ind1=" " ind2="7">
        <subfield code="a">Informatique</subfield>
        <subfield code="0">(RERO)A001234567</subfield>
        <subfield code="2">rero</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    mock_get_mef_link.return_value = "https://mef.rero.ch/api/concepts/rero/A001234567"
    data = marc21.do(marc21json)
    assert data.get("subjects") == [{"entity": {"$ref": "https://mef.rero.ch/api/concepts/rero/A001234567"}}]
    assert data.get("subjects_imported") is None
