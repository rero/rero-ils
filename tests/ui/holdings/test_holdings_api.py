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


"""Holding Record tests."""


from __future__ import absolute_import, print_function

from utils import flush_index, get_mapping

from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.holdings.api import holding_id_fetcher as fetcher
from rero_ils.modules.items.views import format_record_call_number


def test_holding_es_mapping(es, db, holding_lib_martigny,
                            holding_lib_martigny_data):
    """Test holding elasticsearch mapping."""
    search = HoldingsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Holding.create(
        holding_lib_martigny_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_holding_create(db, es_clear, document, org_martigny,
                        loc_public_martigny, item_type_standard_martigny,
                        holding_lib_martigny_data):
    """Test holding creation."""
    holding = Holding.create(holding_lib_martigny_data, dbcommit=True,
                             reindex=True, delete_pid=True)
    flush_index(HoldingsSearch.Meta.index)
    assert holding == holding_lib_martigny_data
    assert holding.get('pid') == '1'

    holding = Holding.get_record_by_pid('1')
    assert holding == holding_lib_martigny_data

    fetched_pid = fetcher(holding.id, holding)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'hold'

    search = HoldingsSearch()
    holding = next(search.filter('term', pid=holding.pid).scan())
    holding_record = Holding.get_record_by_pid(holding.pid)
    assert holding_record.organisation_pid == org_martigny.get('pid')


def test_holdings_call_number_filter(app):
    """Test call number format."""
    holding = {'call_number': 'first_cn'}
    results = 'first_cn'
    assert results == format_record_call_number(holding)

    holding = {'call_number': 'first_cn', 'second_call_number': 'second_cn'}
    results = 'first_cn | second_cn'
    assert results == format_record_call_number(holding)

    holding = {'second_call_number': 'second_cn'}
    results = 'second_cn'
    assert results == format_record_call_number(holding)
