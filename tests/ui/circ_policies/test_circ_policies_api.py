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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from utils import get_mapping

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, \
    CircPolicy, circ_policy_id_fetcher


def test_circ_policy_create(db, circ_policy_data_tmp):
    """Test cipoanisation creation."""
    cipo = CircPolicy.create(circ_policy_data_tmp, delete_pid=True)
    assert cipo == circ_policy_data_tmp
    assert cipo.get('pid') == '1'

    cipo = CircPolicy.get_record_by_pid('1')
    assert cipo == circ_policy_data_tmp

    fetched_pid = circ_policy_id_fetcher(cipo.id, cipo)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'cipo'

    circ_policy = deepcopy(circ_policy_data_tmp)
    del circ_policy['$schema']
    cipo = CircPolicy.create(circ_policy, delete_pid=True)
    assert cipo.get('$schema')
    assert cipo.get('pid') == '2'


def test_circ_policy_es_mapping(es, db, organisation, circ_policy_data_tmp):
    """."""
    search = CircPoliciesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    CircPolicy.create(
        circ_policy_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_circ_policy_exist_name_and_organisation_pid(circ_policy):
    """."""
    cipo = circ_policy.replace_refs()
    assert CircPolicy.exist_name_and_organisation_pid(
        cipo.get('name'), cipo.get('organisation', {}).get('pid'))
    assert not CircPolicy.exist_name_and_organisation_pid(
        'not exists yet', cipo.get('organisation', {}).get('pid'))
