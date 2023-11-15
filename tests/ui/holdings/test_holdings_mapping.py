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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Holdingss record mapping tests."""
from utils import get_mapping

from rero_ils.modules.holdings.api import Holding, HoldingsSearch


def test_holding_es_mapping(search, db, loc_public_martigny,
                            item_type_standard_martigny,
                            document, holding_lib_martigny_data):
    """Test holding elasticsearch mapping."""
    search = HoldingsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    holding = Holding.create(
        holding_lib_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
    # clean created data
    holding.delete(force=True, dbcommit=True, delindex=True)
