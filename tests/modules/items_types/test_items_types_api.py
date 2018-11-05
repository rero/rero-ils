# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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

"""API tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.items_types.api import ItemType, ItemTypeSearch
from rero_ils.utils_test import es_flush_and_refresh


def test_item_type_search():
    """Validate index name."""
    assert 'items_types' == ItemTypeSearch.Meta.index


def test_can_delete():
    """Can Delete."""
    assert ItemType.can_delete


def test_exist_name_and_organisation_pid(app, minimal_item_type_record):
    """Test for exist name and organisation pid."""
    item_type = ItemType.create(
        minimal_item_type_record,
        dbcommit=True,
        reindex=True
    )
    es_flush_and_refresh()

    result = ItemType.exist_name_and_organisation_pid(
        item_type.get('name'),
        item_type.get('organisation_pid')
    )
    assert result

    result = ItemType.exist_name_and_organisation_pid(
        'NEW NAME',
        '1'
    )
    assert result is None
