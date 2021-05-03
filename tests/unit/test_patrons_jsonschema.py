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


def test_required(patron_schema, patron_martigny_data_tmp_with_id):
    """Test required for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_schema)
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_pid(patron_schema, patron_martigny_data_tmp_with_id):
    """Test pid for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['pid'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_first_name(patron_schema, patron_martigny_data_tmp_with_id):
    """Test first_name for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['first_name'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_last_name(patron_schema, patron_martigny_data_tmp_with_id):
    """Test last_name for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['last_name'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_street(patron_schema, patron_martigny_data_tmp_with_id):
    """Test street for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['street'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_postal_code(patron_schema, patron_martigny_data_tmp_with_id):
    """Test postal_code for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['postal_code'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_city(patron_schema, patron_martigny_data_tmp_with_id):
    """Test city for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['city'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_barcode(patron_schema, patron_martigny_data_tmp_with_id):
    """Test barcode for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['patron']['barcode'][0] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_birth_date(patron_schema, patron_martigny_data_tmp_with_id):
    """Test birth date for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['birth_date'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_phone(patron_schema, patron_martigny_data_tmp_with_id):
    """Test phone for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['home_phone'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_patron_type(patron_schema, patron_martigny_data_tmp_with_id):
    """Test patron_type for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['patron_type_pid'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_roles(patron_schema, patron_martigny_data_tmp_with_id):
    """Test roles for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['roles'] = 'text'
        validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_blocked(patron_schema, patron_martigny_data_tmp_with_id):
    """Test blocked field for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    # blocked is a boolean field, should fail with everything except boolean
    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['patron']['blocked'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['patron']['blocked'] = 'text'
        validate(patron_martigny_data_tmp_with_id, patron_schema)

    # Should pass with boolean
    patron_martigny_data_tmp_with_id['patron']['blocked'] = False
    validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_blocked_note(patron_schema, patron_martigny_data_tmp_with_id):
    """Test blocked_note field for patron jsonschemas."""
    validate(patron_martigny_data_tmp_with_id, patron_schema)

    # blocked_note is text field. Should fail except with text.
    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['patron']['blocked_note'] = 25
        validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['patron']['blocked_note'] = True
        validate(patron_martigny_data_tmp_with_id, patron_schema)

    patron_martigny_data_tmp_with_id['patron']['blocked_note'] = 'Lost card'
    validate(patron_martigny_data_tmp_with_id, patron_schema)


def test_local_codes(patron_schema, patron_martigny_data_tmp_with_id):
    """Test local codes for patron jsonschemas."""

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['local_codes'] = 'data'
        validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['local_codes'] = ['data', 12]
        validate(patron_martigny_data_tmp_with_id, patron_schema)

    with pytest.raises(ValidationError):
        patron_martigny_data_tmp_with_id['local_codes'] = ['data', 'data']
        validate(patron_martigny_data_tmp_with_id, patron_schema)
