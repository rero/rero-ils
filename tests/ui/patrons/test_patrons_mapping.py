# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Patron elasticsearch mapping tests."""

from utils import get_mapping

from rero_ils.modules.patrons.api import Patron, PatronsSearch


def test_patron_search_mapping(
    app, patrons_records
):
    """Test patron search mapping."""
    search = PatronsSearch()

    c = search.query('query_string', query='Casalini').count()
    assert c == 1

    c = search.query('match', first_name='Simonetta').count()
    assert c == 1

    c = search.query('match', last_name='Rodriguez').count()
    assert c == 1

    c = search.query('match', first_name='Eléna').count()
    assert c == 1

    c = search.query('match', first_name='Elena').count()
    assert c == 1

    pids = [r.pid for r in search.query(
         'match', first_name='Eléna').source(['pid']).scan()]
    assert 'ptrn4' in pids


def test_patron_es_mapping(
        roles, es_clear, lib_martigny, librarian_martigny_data_tmp):
    """Test patron elasticsearch mapping."""
    search = PatronsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)
