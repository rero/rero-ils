# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Local fields JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_local_fields_fields_required(local_fields_schema, local_field_martigny_data):
    """Test required for local fields jsonschemas."""
    record = copy.deepcopy(local_field_martigny_data)
    validate(record, local_fields_schema)

    # Check minlength
    with pytest.raises(ValidationError):
        record["fields"] = ["12"]
        validate(record, local_fields_schema)

    # Check missing fields
    with pytest.raises(ValidationError):
        del record["fields"]
        validate(record, local_fields_schema)

    # Check empty schema
    with pytest.raises(ValidationError):
        validate({}, local_fields_schema)


def test_local_fields_all_jsonschema_keys_values(
    local_fields_schema, local_field_martigny_data
):
    """Test all keys and values for local fields jsonschema."""
    record = copy.deepcopy(local_field_martigny_data)
    validate(record, local_fields_schema)
    validator = [
        {"key": "pid", "value": 25},
        {"key": "organisation", "value": 25},
        {"key": "parent", "value": 25},
    ]
    for element in validator:
        with pytest.raises(ValidationError):
            record[element["key"]] = element["value"]
            validate(record, local_fields_schema)
