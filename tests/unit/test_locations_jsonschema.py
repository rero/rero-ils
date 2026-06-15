# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Location JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.api import ils_record_format_checker


def test_locations_required(location_schema, loc_public_martigny_data):
    """Test required for location jsonschemas."""
    validate(loc_public_martigny_data, location_schema)

    with pytest.raises(ValidationError):
        validate({}, location_schema)


def test_locations_pid(location_schema, loc_public_martigny_data):
    """Test pid for location jsonschemas."""
    validate(loc_public_martigny_data, location_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(loc_public_martigny_data)
        data["pid"] = 25
        validate(data, location_schema)


def test_locations_name(location_schema, loc_public_martigny_data):
    """Test name for location jsonschemas."""
    validate(loc_public_martigny_data, location_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(loc_public_martigny_data)
        data["name"] = 25
        validate(data, location_schema)


def test_locations_email(location_schema, loc_public_martigny_data):
    """Test email for location jsonschemas."""
    data = loc_public_martigny_data

    data["notification_email"] = "test@test.@be"
    with pytest.raises(ValidationError):
        validate(data, location_schema, format_checker=ils_record_format_checker)
