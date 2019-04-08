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

"""Circulation policies tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import mock
from utils import get_mapping

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, \
    CircPolicy, circ_policy_id_fetcher


def test_no_default_policy(app):
    """Test when no default circulation policy configured."""
    cipo = CircPolicy.get_default_circ_policy()
    assert not cipo


def test_circ_policy_create(db, circ_policy_martigny_data_tmp):
    """Test circulation policy creation."""
    cipo = CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)
    assert cipo == circ_policy_martigny_data_tmp
    assert cipo.get('pid') == '1'

    cipo = CircPolicy.get_record_by_pid('1')
    assert cipo == circ_policy_martigny_data_tmp

    fetched_pid = circ_policy_id_fetcher(cipo.id, cipo)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'cipo'

    circ_policy = deepcopy(circ_policy_martigny_data_tmp)
    del circ_policy['$schema']
    cipo = CircPolicy.create(circ_policy, delete_pid=True)
    assert cipo.get('$schema')
    assert cipo.get('pid') == '2'


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


def test_circ_policy_exist_name_and_organisation_pid(
        circ_policy_default_martigny):
    """Test policy name existance."""
    circ_policy = circ_policy_default_martigny
    cipo = circ_policy.replace_refs()
    assert CircPolicy.exist_name_and_organisation_pid(
        cipo.get('name'), cipo.get('organisation', {}).get('pid'))
    assert not CircPolicy.exist_name_and_organisation_pid(
        'not exists yet', cipo.get('organisation', {}).get('pid'))


def test_circ_policy_can_not_delete(circ_policy_default_martigny,
                                    circ_policy_short_martigny):
    """Test can not delete a policy."""
    others = circ_policy_default_martigny.get_non_link_reasons_to_not_delete()
    assert others['is_default']
    assert not circ_policy_default_martigny.can_delete

    others = circ_policy_short_martigny.get_non_link_reasons_to_not_delete()
    assert 'is_default' not in others
    assert not circ_policy_short_martigny.can_delete
    assert others['has_settings']


def test_circ_policy_can_delete(app, circ_policy_martigny_data_tmp):
    """Test can delete a policy."""
    circ_policy_martigny_data_tmp['is_default'] = False
    cipo = CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)
    assert cipo.get_links_to_me() == {}
    assert cipo.can_delete

    reasons = cipo.reasons_not_to_delete()
    assert 'links' not in reasons

    with mock.patch(
            'rero_ils.modules.circ_policies.api.CircPolicy.get_links_to_me'
    ) as a:
            a.return_value = {'object': 1}
            reasons = cipo.reasons_not_to_delete()
            assert 'links' in reasons
