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
