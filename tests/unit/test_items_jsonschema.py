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

"""item JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.items.models import ItemNoteTypes


def test_required(item_schema, item_lib_martigny_data_tmp):
    """Test required for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)

    with pytest.raises(ValidationError):
        validate({}, item_schema)


def test_pid(item_schema, item_lib_martigny_data_tmp):
    """Test pid for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)

    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['pid'] = 25
        validate(item_lib_martigny_data_tmp, item_schema)


def test_barcode(item_schema, item_lib_martigny_data_tmp):
    """Test barcode for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)

    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['barcode'] = 2
        validate(item_lib_martigny_data_tmp, item_schema)


def test_call_number(item_schema, item_lib_martigny_data_tmp):
    """Test call_number for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)

    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['callNumber'] = 25
        validate(item_lib_martigny_data_tmp, item_schema)


def test_location(item_schema, item_lib_martigny_data_tmp):
    """Test location for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)

    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['location'] = 25
        validate(item_lib_martigny_data_tmp, item_schema)


def test_item_type(item_schema, item_lib_martigny_data_tmp):
    """Test location for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)

    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['item_type_pid'] = 25
        validate(item_lib_martigny_data_tmp, item_schema)


def test_item_notes(item_schema, item_lib_martigny_data_tmp):
    """Test notes for item jsonschemas."""
    validate(item_lib_martigny_data_tmp, item_schema)
    item_lib_martigny_data_tmp['notes'] = []

    public_note = dict(type=ItemNoteTypes.PUBLIC, content='public note')
    staff_note = dict(type=ItemNoteTypes.STAFF, content='staff note')
    dummy_note = dict(type='dummy', content='dummy note')
    long_note = dict(type=ItemNoteTypes.CHECKIN, content='note' * 501)

    item_lib_martigny_data_tmp['notes'] = [public_note]
    validate(item_lib_martigny_data_tmp, item_schema)

    item_lib_martigny_data_tmp['notes'] = [public_note, staff_note]
    validate(item_lib_martigny_data_tmp, item_schema)

    # add a not-valid note type should raise a validation error
    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['notes'] = [dummy_note]
        validate(item_lib_martigny_data_tmp, item_schema)

    # add a too long note content
    with pytest.raises(ValidationError):
        item_lib_martigny_data_tmp['notes'] = [long_note]
        validate(item_lib_martigny_data_tmp, item_schema)
