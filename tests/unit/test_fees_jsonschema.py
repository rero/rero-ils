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

"""Fees JSON schema tests."""


import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(fee_schema, dummy_fee):
    """Test required for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        validate({}, fee_schema)
        validate(dummy_fee, fee_schema)


def test_pid(fee_schema, dummy_fee):
    """Test pid for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['pid'] = 25
        validate(dummy_fee, fee_schema)


def test_fee_type(
        fee_schema, dummy_fee):
    """Test type for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['fee_type'] = 25
        validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['fee_type'] = 'test'
        validate(dummy_fee, fee_schema)


def test_amount(fee_schema, dummy_fee):
    """Test amount for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['amount'] = 'test'
        validate(dummy_fee, fee_schema)


def test_currency(fee_schema, dummy_fee):
    """Test currency for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['currency'] = 25
        validate(dummy_fee, fee_schema)
    with pytest.raises(ValidationError):
        dummy_fee['currency'] = 'YEN'
        validate(dummy_fee, fee_schema)


def test_status(fee_schema, dummy_fee):
    """Test status for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['status'] = 25
        validate(dummy_fee, fee_schema)
    with pytest.raises(ValidationError):
        dummy_fee['status'] = 'test'
        validate(dummy_fee, fee_schema)


def test_location(fee_schema, dummy_fee):
    """Test location for fee jsonschemas."""
    validate(dummy_fee, fee_schema)

    with pytest.raises(ValidationError):
        dummy_fee['location'] = 25
        validate(dummy_fee, fee_schema)
