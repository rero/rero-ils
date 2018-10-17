# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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


def test_required(patron_type_schema, minimal_patron_type_record):
    """Test required for patron jsonschemas."""
    validate(minimal_patron_type_record, patron_type_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_type_schema)
        validate(minimal_patron_type_record, patron_type_schema)


def test_pid(patron_type_schema, minimal_patron_type_record):
    """Test pid for patron type jsonschemas."""
    validate(minimal_patron_type_record, patron_type_schema)

    with pytest.raises(ValidationError):
        minimal_patron_type_record['pid'] = 25
        validate(minimal_patron_type_record, patron_type_schema)


def test_name(patron_type_schema, minimal_patron_type_record):
    """Test name for patron type jsonschemas."""
    validate(minimal_patron_type_record, patron_type_schema)

    with pytest.raises(ValidationError):
        minimal_patron_type_record['name'] = 25
        validate(minimal_patron_type_record, patron_type_schema)


def test_description(patron_type_schema, minimal_patron_type_record):
    """Test description for patron type jsonschemas."""
    validate(minimal_patron_type_record, patron_type_schema)

    with pytest.raises(ValidationError):
        minimal_patron_type_record['description'] = 25
        validate(minimal_patron_type_record, patron_type_schema)


def test_organisation_pid(patron_type_schema, minimal_patron_type_record):
    """Test organisation_pid for patron type jsonschemas."""
    validate(minimal_patron_type_record, patron_type_schema)

    with pytest.raises(ValidationError):
        minimal_patron_type_record['organisation_pid'] = 25
        validate(minimal_patron_type_record, patron_type_schema)
