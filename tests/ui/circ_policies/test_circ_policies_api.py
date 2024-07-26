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

"""Circulation policies tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.circ_policies.api import CircPolicy, \
    circ_policy_id_fetcher


def test_no_default_policy(app):
    """Test when no default circulation policy configured."""
    cipo = CircPolicy.get_default_circ_policy('org1')
    assert not cipo


def test_circ_policy_create(circ_policy_martigny_data_tmp,
                            circ_policy_short_martigny_data,
                            org_martigny,
                            lib_martigny, lib_saxon,
                            patron_type_children_martigny,
                            item_type_standard_martigny,
                            patron_type_adults_martigny,
                            item_type_specific_martigny,
                            item_type_regular_sion,
                            patron_type_youngsters_sion):
    """Test circulation policy creation."""
    cipo = CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)
    assert cipo == circ_policy_martigny_data_tmp
    assert cipo.get('pid') == '1'

    cipo = CircPolicy.get_record_by_pid('1')
    assert cipo == circ_policy_martigny_data_tmp

    fetched_pid = circ_policy_id_fetcher(cipo.id, cipo)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'cipo'

    circ_policy_data = deepcopy(circ_policy_short_martigny_data)
    del circ_policy_data['$schema']
    cipo = CircPolicy.create(circ_policy_data, delete_pid=True)
    assert cipo.get('$schema')
    assert cipo.get('pid') == '2'

    cipo_data = {
        '$schema': 'https://bib.rero.ch/schemas/'
        'circ_policies/circ_policy-v0.0.1.json',
        'pid': 'cipo_test',
        'name': 'test',
        'organisation': {
            '$ref': 'https://bib.rero.ch/api/organisations/org1'
        },
        'is_default': False,
        'allow_requests': True,
        'policy_library_level': False,
        'settings': [{
            'patron_type': {
                '$ref': 'https://bib.rero.ch/api/patron_types/ptty3'
            },
            'item_type': {
                '$ref': 'https://bib.rero.ch/api/item_types/itty1'
            }
        }, {
            'patron_type': {
                '$ref': 'https://bib.rero.ch/api/patron_types/ptty2'
            },
            'item_type': {
                '$ref': 'https://bib.rero.ch/api/item_types/itty4'
            }
        }]
    }
    with pytest.raises(ValidationError):
        cipo = CircPolicy.create(cipo_data, delete_pid=False)

    # TEST #2 : create a second defaut policy
    #   The first created policy (pid=1) is the default policy.
    #   Creation of a second default policy should raise a ValidationError
    default_cipo = CircPolicy.get_record_by_pid('1')
    assert default_cipo.get('is_default')
    with pytest.raises(ValidationError) as excinfo:
        CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)
    assert 'CircPolicy: already a default policy for this org' \
           in str(excinfo.value)


def test_circ_policy_exist_name_and_organisation_pid(
        circ_policy_short_martigny):
    """Test policy name existence."""
    cipo = circ_policy_short_martigny.replace_refs()
    assert CircPolicy.exist_name_and_organisation_pid(
        cipo.get('name'), cipo.get('organisation', {}).get('pid'))
    assert not CircPolicy.exist_name_and_organisation_pid(
        'not exists yet', cipo.get('organisation', {}).get('pid'))


def test_circ_policy_can_not_delete(circ_policy_short_martigny):
    """Test can not delete a policy."""
    org_pid = circ_policy_short_martigny.organisation_pid
    defaut_cipo = CircPolicy.get_default_circ_policy(org_pid)
    can, reasons = defaut_cipo.can_delete
    assert not can
    assert reasons['others']['is_default']

    can, reasons = circ_policy_short_martigny.can_delete
    assert can
    assert reasons == {}


def test_circ_policy_can_delete(app, circ_policy_martigny_data_tmp):
    """Test can delete a policy."""
    circ_policy_martigny_data_tmp['is_default'] = False
    cipo = CircPolicy.create(circ_policy_martigny_data_tmp, delete_pid=True)

    can, reasons = cipo.can_delete
    assert can
    assert reasons == {}


def test_circ_policy_extended_validation(
    app,
    circ_policy_short_martigny,
    circ_policy_short_martigny_data,
    circ_policy_default_sion_data
):
    """Test extended validation for circ policy"""
    cipo_data = deepcopy(circ_policy_short_martigny_data)
    cipo_data['allow_requests'] = False
    cipo_data['pickup_hold_duration'] = 10
    del cipo_data['pid']

    cipo = CircPolicy.create(cipo_data)
    assert cipo
    assert 'pickup_hold_duration' not in cipo

    cipo.delete()

    # Check that I cannot save a CiPo without a renewal duration if
    # renewals are enabled.
    cipo_sion_data = deepcopy(circ_policy_default_sion_data)
    assert cipo_sion_data['number_renewals'] > 0

    cipo_sion_data.pop('renewal_duration')

    with pytest.raises(ValidationError) as err:
        CircPolicy.create(cipo_sion_data, delete_pid=True)
    assert 'renewal duration is required' in str(err.value)
