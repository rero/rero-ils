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

"""patron JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(circ_policy_schema, minimal_circ_policy_record):
    """Test required for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        validate({}, circ_policy_schema)
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_pid(circ_policy_schema, minimal_circ_policy_record):
    """Test pid for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['pid'] = 25
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_name(circ_policy_schema, minimal_circ_policy_record):
    """Test name for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['name'] = 25
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_desc(circ_policy_schema, minimal_circ_policy_record):
    """Test description for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['description'] = 25
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_org(circ_policy_schema, minimal_circ_policy_record):
    """Test organisation pid for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['organisation_pid'] = 25
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_renewal_duration(
    circ_policy_schema, minimal_circ_policy_record
):
    """Test renewal_duration for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['renewal_duration'] = '25'
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_allow_checkout(
    circ_policy_schema, minimal_circ_policy_record
):
    """Test allow_checkout for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['allow_checkout'] = 25
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_checkout_duration(
    circ_policy_schema, minimal_circ_policy_record
):
    """Test checkout_duration for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['checkout_duration'] = '25'
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_allow_requests(
    circ_policy_schema, minimal_circ_policy_record
):
    """Test allow_requests for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['allow_requests'] = 25
        validate(minimal_circ_policy_record, circ_policy_schema)


def test_circ_policy_number_renewals(
    circ_policy_schema, minimal_circ_policy_record
):
    """Test number_renewals for circ policy jsonschema."""
    validate(minimal_circ_policy_record, circ_policy_schema)

    with pytest.raises(ValidationError):
        minimal_circ_policy_record['number_renewals'] = '25'
        validate(minimal_circ_policy_record, circ_policy_schema)
