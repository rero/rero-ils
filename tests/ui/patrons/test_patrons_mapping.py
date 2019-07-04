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

"""Patron elasticsearch mapping tests."""

from utils import get_mapping

from rero_ils.modules.patrons.api import Patron, PatronsSearch


def test_patron_search_mapping(
    app, patrons_records, librarian_saxon_no_email
):
    """Test patron search mapping."""
    search = PatronsSearch()

    c = search.query('query_string', query='Roduit').count()
    assert c == 1

    c = search.query('match', first_name='Eric').count()
    assert c == 1

    c = search.query('match', last_name='Moret').count()
    assert c == 1

    c = search.query('match', first_name='Eléna').count()
    assert c == 1

    c = search.query('match', first_name='Elena').count()
    assert c == 1

    pids = [r.pid for r in search.query(
         'match', first_name='Eléna').source(['pid']).scan()]
    assert librarian_saxon_no_email.pid in pids


def test_patron_es_mapping(
        roles, es_clear, lib_martigny, librarian_martigny_data_tmp):
    """Test patron elasticsearch mapping."""
    search = PatronsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)
