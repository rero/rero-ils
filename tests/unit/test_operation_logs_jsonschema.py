# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Operation log JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(operation_log_schema, operation_log_data):
    """Test required for operation log jsonschemas."""
    validate(operation_log_data, operation_log_schema)

    with pytest.raises(ValidationError):
        validate({}, operation_log_schema)


def test_operation_log_all_jsonschema_keys_values(operation_log_schema, operation_log_data):
    """Test all keys and values for operation log jsonschema."""
    record = operation_log_data
    validate(record, operation_log_schema)
    validator = [
        {"key": "pid", "value": 25},
        {"key": "operation", "value": 25},
        {"key": "record", "value": 25},
        {"key": "date", "value": 25},
        {"key": "organisation", "value": 25},
        {"key": "user", "value": 25},
        {"key": "user_name", "value": 25},
    ]
    for element in validator:
        with pytest.raises(ValidationError):
            record[element["key"]] = element["value"]
            validate(record, operation_log_schema)
