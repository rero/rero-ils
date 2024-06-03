# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Test explain."""

from rero_ils.modules.sru.explaine import Explain


def test_explain(app):
    """Test Explain."""
    explain = Explain("api/sru")
    explain_strings = str(explain).split("\n")
    assert (
        explain_strings[0]
        == '<sru:explainResponse xmlns:sru="http://www.loc.gov/standards/sru/">'
    )
    assert explain.database == "api/sru"
    assert explain.number_of_records == app.config.get("RERO_SRU_NUMBER_OF_RECORDS")
    assert explain.maximum_records == app.config.get("RERO_SRU_MAXIMUM_RECORDS")
    assert explain.doc_type == "doc"
    assert explain.index == app.config.get("RECORDS_REST_ENDPOINTS", {}).get(
        "doc", {}
    ).get("search_index")
