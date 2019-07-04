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

"""Patron type elasticsearch mapping tests."""

from utils import get_mapping

from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch


def test_patron_types_search_mapping(
    app, patron_types_records
):
    """Test patron type search mapping."""
    search = PatronTypesSearch()

    c = search.query('query_string', query='patrons').count()
    assert c == 4

    c = search.query('match', name='patrons').count()
    assert c == 0

    c = search.query('match', name='children').count()
    assert c == 1

    pids = [r.pid for r in search.query(
         'match', name='children').source(['pid']).scan()]
    assert 'ptty1' in pids


def test_patron_type_es_mapping(es_clear, db, org_martigny,
                                patron_type_children_martigny_data):
    """Test patron types es mapping."""
    search = PatronTypesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    PatronType.create(
        patron_type_children_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
