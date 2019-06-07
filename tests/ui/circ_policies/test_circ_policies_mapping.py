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

"""Circulation Policy Record tests."""

from utils import get_mapping

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy


def test_circ_policies_search_mapping(
    app, circulation_policies
):
    """Test circulation policy search mapping."""
    search = CircPoliciesSearch()

    c = search.query('query_string', query='policy').count()
    assert c == 4

    c = search.query('match', name='default').count()
    assert c == 2

    c = search.query('match', description='temporary').count()
    assert c == 1

    pids = [r.pid for r in search.query(
         'match', name='temporary').source(['pid']).scan()]
    assert 'cipo3' in pids


def test_circ_policy_es_mapping(es, db, org_martigny,
                                circ_policy_martigny_data_tmp):
    """Test circulation policy elasticsearch mapping."""
    search = CircPoliciesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    CircPolicy.create(
        circ_policy_martigny_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
