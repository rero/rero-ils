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

"""Item type elasticsearch mapping tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.item_types.api import ItemType, ItemTypesSearch


def test_item_type_es_mapping(es_clear, db, org_martigny, item_type_data_tmp):
    """Test item type elasticsearch mapping."""
    search = ItemTypesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    ItemType.create(
        item_type_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_item_types_search_mapping(
    app, item_types_records
):
    """Test item type search mapping."""
    search = ItemTypesSearch()

    c = search.query('query_string', query='checkout').count()
    assert c == 2

    c = search.query('match', name='checkout').count()
    assert c == 0

    c = search.query('match', name='specific').count()
    assert c == 1

    pids = [r.pid for r in search.query(
         'match', name='specific').source(['pid']).scan()]
    assert 'itty3' in pids
