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

"""Item type JSONResolver tests."""

import pytest
from invenio_records.api import Record
from jsonref import JsonRefError


def test_item_types_jsonresolver(item_type_standard_martigny):
    """Item type resolver tests."""
    rec = Record.create({
        'item_type': {'$ref': 'https://ils.rero.ch/api/item_types/itty1'}
    })
    assert rec.replace_refs().get('item_type') == {'pid': 'itty1'}

    # deleted record
    item_type_standard_martigny.delete()
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()

    # non existing record
    rec = Record.create({
        'item_type': {'$ref': 'https://ils.rero.ch/api/item_types/n_e'}
    })
    with pytest.raises(JsonRefError):
        rec.replace_refs().dumps()
