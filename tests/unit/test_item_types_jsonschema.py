# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""patron JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(item_type_schema, item_type_data_tmp):
    """Test required for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        validate({}, item_type_schema)
        validate(item_type_data_tmp, item_type_schema)


def test_pid(item_type_schema, item_type_data_tmp):
    """Test pid for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp["pid"] = 25
        validate(item_type_data_tmp, item_type_schema)


def test_name(item_type_schema, item_type_data_tmp):
    """Test name for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp["name"] = 25
        validate(item_type_data_tmp, item_type_schema)


def test_description(item_type_schema, item_type_data_tmp):
    """Test description for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp["description"] = 25
        validate(item_type_data_tmp, item_type_schema)


def test_organisation_pid(item_type_schema, item_type_data_tmp):
    """Test organisation_pid for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp["organisation_pid"] = 25
        validate(item_type_data_tmp, item_type_schema)
