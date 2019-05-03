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

"""Circulation policies JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(circ_policy_schema, circ_policy_data_tmp):
    """Test required for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        validate({}, circ_policy_schema)
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_pid(circ_policy_schema, circ_policy_data_tmp):
    """Test pid for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['pid'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_name(circ_policy_schema, circ_policy_data_tmp):
    """Test name for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['name'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_desc(circ_policy_schema, circ_policy_data_tmp):
    """Test description for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['description'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_org(circ_policy_schema, circ_policy_data_tmp):
    """Test organisation pid for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['organisation_pid'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_renewal_duration(
    circ_policy_schema, circ_policy_data_tmp
):
    """Test renewal_duration for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['renewal_duration'] = '25'
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_allow_checkout(
    circ_policy_schema, circ_policy_data_tmp
):
    """Test allow_checkout for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['allow_checkout'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_checkout_duration(
    circ_policy_schema, circ_policy_data_tmp
):
    """Test checkout_duration for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['checkout_duration'] = '25'
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_allow_requests(
    circ_policy_schema, circ_policy_data_tmp
):
    """Test allow_requests for circcirculation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['allow_requests'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_number_renewals(
    circ_policy_schema, circ_policy_data_tmp
):
    """Test number_renewals for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)

    with pytest.raises(ValidationError):
        circ_policy_data_tmp['number_renewals'] = '25'
        validate(circ_policy_data_tmp, circ_policy_schema)


def test_circ_policy_is_default(
    circ_policy_schema, circ_policy_data_tmp
):
    """Test is_default for circulation policy jsonschema."""
    validate(circ_policy_data_tmp, circ_policy_schema)
    with pytest.raises(ValidationError):
        circ_policy_data_tmp['is_default'] = 25
        validate(circ_policy_data_tmp, circ_policy_schema)
