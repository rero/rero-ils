# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
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


def test_required(patron_schema, minimal_patron_record):
    """Test required for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_schema)
        validate(minimal_patron_record, patron_schema)


def test_pid(patron_schema, minimal_patron_record):
    """Test pid for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['pid'] = 25
        validate(minimal_patron_record, patron_schema)


def test_first_name(patron_schema, minimal_patron_record):
    """Test first_name for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['first_name'] = 25
        validate(minimal_patron_record, patron_schema)


def test_last_name(patron_schema, minimal_patron_record):
    """Test last_name for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['last_name'] = 25
        validate(minimal_patron_record, patron_schema)


def test_street(patron_schema, minimal_patron_record):
    """Test street for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['street'] = 25
        validate(minimal_patron_record, patron_schema)


def test_postal_code(patron_schema, minimal_patron_record):
    """Test postal_code for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['postal_code'] = 25
        validate(minimal_patron_record, patron_schema)


def test_city(patron_schema, minimal_patron_record):
    """Test city for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['city'] = 25
        validate(minimal_patron_record, patron_schema)


def test_barcode(patron_schema, minimal_patron_record):
    """Test barcode for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['barcode'] = 25
        validate(minimal_patron_record, patron_schema)


def test_birth_date(patron_schema, minimal_patron_record):
    """Test birth date for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['birth_date'] = 25
        validate(minimal_patron_record, patron_schema)


def test_email(patron_schema, minimal_patron_record):
    """Test email for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['email'] = 25
        validate(minimal_patron_record, patron_schema)


def test_phone(patron_schema, minimal_patron_record):
    """Test phone for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['phone'] = 25
        validate(minimal_patron_record, patron_schema)


def test_patron_type(patron_schema, minimal_patron_record):
    """Test patron_type for patron jsonschema."""
    validate(minimal_patron_record, patron_schema)

    with pytest.raises(ValidationError):
        minimal_patron_record['patron_type'] = 25
        validate(minimal_patron_record, patron_schema)
