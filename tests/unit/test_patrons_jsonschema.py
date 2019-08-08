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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Patron JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(patron_schema, librarian_martigny_data_tmp):
    """Test required for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_schema)
        validate(librarian_martigny_data_tmp, patron_schema)


def test_pid(patron_schema, librarian_martigny_data_tmp):
    """Test pid for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['pid'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_first_name(patron_schema, librarian_martigny_data_tmp):
    """Test first_name for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['first_name'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_last_name(patron_schema, librarian_martigny_data_tmp):
    """Test last_name for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['last_name'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_street(patron_schema, librarian_martigny_data_tmp):
    """Test street for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['street'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_postal_code(patron_schema, librarian_martigny_data_tmp):
    """Test postal_code for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['postal_code'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_city(patron_schema, librarian_martigny_data_tmp):
    """Test city for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['city'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_barcode(patron_schema, librarian_martigny_data_tmp):
    """Test barcode for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['barcode'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_birth_date(patron_schema, librarian_martigny_data_tmp):
    """Test birth date for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['birth_date'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_email(patron_schema, librarian_martigny_data_tmp):
    """Test email for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['email'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_phone(patron_schema, librarian_martigny_data_tmp):
    """Test phone for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['phone'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_patron_type(patron_schema, librarian_martigny_data_tmp):
    """Test patron_type for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['patron_type_pid'] = 25
        validate(librarian_martigny_data_tmp, patron_schema)


def test_roles(patron_schema, librarian_martigny_data_tmp):
    """Test roles for patron jsonschemas."""
    validate(librarian_martigny_data_tmp, patron_schema)

    with pytest.raises(ValidationError):
        librarian_martigny_data_tmp['roles'] = 'text'
        validate(librarian_martigny_data_tmp, patron_schema)
