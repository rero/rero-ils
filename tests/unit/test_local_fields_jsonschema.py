# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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


def test_local_fields_all_jsonschema_keys_values(local_fields_schema, local_field_martigny_data):
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
