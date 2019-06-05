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
