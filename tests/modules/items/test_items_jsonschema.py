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

"""item JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(item_schema, limited_item_record):
    """Test required for item jsonschemas."""
    validate(limited_item_record, item_schema)

    with pytest.raises(ValidationError):
        validate({}, item_schema)


def test_pid(item_schema, limited_item_record):
    """Test pid for item jsonschemas."""
    validate(limited_item_record, item_schema)

    with pytest.raises(ValidationError):
        limited_item_record['pid'] = 25
        validate(limited_item_record, item_schema)


def test_barcode(item_schema, limited_item_record):
    """Test barcode for item jsonschemas."""
    validate(limited_item_record, item_schema)

    with pytest.raises(ValidationError):
        limited_item_record['barcode'] = 2
        validate(limited_item_record, item_schema)


def test_call_number(item_schema, limited_item_record):
    """Test call_number for item jsonschemas."""
    validate(limited_item_record, item_schema)

    with pytest.raises(ValidationError):
        limited_item_record['callNumber'] = 25
        validate(limited_item_record, item_schema)


def test_location(item_schema, limited_item_record):
    """Test location for item jsonschemas."""
    validate(limited_item_record, item_schema)

    with pytest.raises(ValidationError):
        limited_item_record['location'] = 25
        validate(limited_item_record, item_schema)


def test_item_type(item_schema, limited_item_record):
    """Test location for item jsonschemas."""
    validate(limited_item_record, item_schema)

    with pytest.raises(ValidationError):
        limited_item_record['item_type_pid'] = 25
        validate(limited_item_record, item_schema)
