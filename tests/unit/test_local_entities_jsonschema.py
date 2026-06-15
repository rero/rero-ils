# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""item JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_validate(local_entities_schema, local_entity_person):
    """Test required for item jsonschemas."""
    validate(local_entity_person, local_entities_schema)
    with pytest.raises(ValidationError):
        validate({}, local_entities_schema)
