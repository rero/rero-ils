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


"""Test temporary items."""

from __future__ import absolute_import, print_function

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus, TypeOfItem
from rero_ils.modules.utils import get_ref_for_pid


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_temporary_items_creation(client, document,
                                  holding_lib_martigny_w_patterns,
                                  temporary_item_lib_martigny_data):
    """Test creation of temporary items."""
    holding = holding_lib_martigny_w_patterns
    temporary_item_lib_martigny_data['holding'] = \
        {'$ref': get_ref_for_pid('hold', holding.pid)}
    item = Item.create(
        temporary_item_lib_martigny_data, dbcommit=True, reindex=True)

    item_url = url_for('invenio_records_rest.item_item', pid_value=item.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    item_es = Item(get_json(res).get('metadata'))
    assert item_es.get('type') == TypeOfItem.TEMPORARY
    assert item_es.status == ItemStatus.ON_SHELF
    assert item_es.holding_pid == holding.pid
