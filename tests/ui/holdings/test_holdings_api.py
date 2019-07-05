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

"""Holding Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.holdings.api import holding_id_fetcher as fetcher


def test_holding_create(db, es_clear, holding_lib_martigny_data):
    """Test holding creation."""
    holding = Holding.create(holding_lib_martigny_data, delete_pid=True)
    assert holding == holding_lib_martigny_data
    assert holding.get('pid') == '1'

    holding = Holding.get_record_by_pid('1')
    assert holding == holding_lib_martigny_data

    fetched_pid = fetcher(holding.id, holding)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'hold'


def test_holding_organisation_pid(org_martigny, holding_lib_martigny):
    """Test organisation pid has been added during the indexing."""
    search = HoldingsSearch()
    holding = next(search.filter('term', pid=holding_lib_martigny.pid).scan())
    holding_record = Holding.get_record_by_pid(holding.pid)
    assert holding_record.organisation_pid == org_martigny.pid


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
