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

"""Patron JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(patron_schema, patron_martigny_data_tmp):
    """Test required for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_schema)
        validate(patron_martigny_data_tmp, patron_schema)


def test_pid(patron_schema, patron_martigny_data_tmp):
    """Test pid for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['pid'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_first_name(patron_schema, patron_martigny_data_tmp):
    """Test first_name for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['first_name'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_last_name(patron_schema, patron_martigny_data_tmp):
    """Test last_name for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['last_name'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_street(patron_schema, patron_martigny_data_tmp):
    """Test street for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['street'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_postal_code(patron_schema, patron_martigny_data_tmp):
    """Test postal_code for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['postal_code'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_city(patron_schema, patron_martigny_data_tmp):
    """Test city for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['city'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_username(patron_schema, patron_martigny_data_tmp):
    """Test username for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)
    del(patron_martigny_data_tmp['username'])
    with pytest.raises(ValidationError):
        validate(patron_martigny_data_tmp, patron_schema)


def test_barcode(patron_schema, patron_martigny_data_tmp):
    """Test barcode for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['patron']['barcode'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_birth_date(patron_schema, patron_martigny_data_tmp):
    """Test birth date for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['birth_date'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_email(patron_schema, patron_martigny_data_tmp):
    """Test email for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    # email is optional
    del patron_martigny_data_tmp['email']
    validate(patron_martigny_data_tmp, patron_schema)

    # email with a bad format
    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['email'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_phone(patron_schema, patron_martigny_data_tmp):
    """Test phone for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['phone'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_patron_type(patron_schema, patron_martigny_data_tmp):
    """Test patron_type for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['patron_type_pid'] = 25
        validate(patron_martigny_data_tmp, patron_schema)


def test_roles(patron_schema, patron_martigny_data_tmp):
    """Test roles for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['roles'] = 'text'
        validate(patron_martigny_data_tmp, patron_schema)


def test_blocked(patron_schema, patron_martigny_data_tmp):
    """Test blocked field for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    # blocked is a boolean field, should fail with everything except boolean
    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['patron']['blocked'] = 25
        validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['patron']['blocked'] = 'text'
        validate(patron_martigny_data_tmp, patron_schema)

    # Should pass with boolean
    patron_martigny_data_tmp['patron']['blocked'] = False
    validate(patron_martigny_data_tmp, patron_schema)


def test_blocked_note(patron_schema, patron_martigny_data_tmp):
    """Test blocked_note field for patron jsonschemas."""
    validate(patron_martigny_data_tmp, patron_schema)

    # blocked_note is text field. Should fail except with text.
    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['patron']['blocked_note'] = 25
        validate(patron_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp['patron']['blocked_note'] = True
        validate(patron_martigny_data_tmp, patron_schema)

    patron_martigny_data_tmp['patron']['blocked_note'] = 'Lost card'
    validate(patron_martigny_data_tmp, patron_schema)
