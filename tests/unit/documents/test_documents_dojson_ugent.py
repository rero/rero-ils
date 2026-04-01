# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2026 RERO
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

"""DOJSON UGent model tests."""

import pytest
from dojson.contrib.marc21.utils import create_record

from rero_ils.modules.documents.dojson.contrib.marc21tojson.ugent import marc21
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


def test_marc21_to_credits_511_prefix():
    """Test that field 511 gets a French-language prefix in credits."""
    marc21xml = """
    <record>
      <datafield tag="511" ind1="0" ind2=" ">
        <subfield code="a">John Doe, Jane Smith</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get("credits") == ["Participants ou interprètes: John Doe, Jane Smith"]


def test_marc21_to_credits_508_no_prefix():
    """Test that field 508 (creation/production credits) gets no prefix."""
    marc21xml = """
    <record>
      <datafield tag="508" ind1=" " ind2=" ">
        <subfield code="a">Photography by John Doe</subfield>
      </datafield>
    </record>
    """
    marc21json = create_record(marc21xml)
    data = marc21.do(marc21json)
    assert data.get("credits") == ["Photography by John Doe"]
