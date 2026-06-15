# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""patron JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(remote_entities_schema, entity_person_data_tmp):
    """Test required for patron jsonschemas."""
    validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate({}, remote_entities_schema)
        validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate(
            {"pid": "ent_pers", "viaf_pid": "56597999", "sources": ["rero", "gnd"]},
            remote_entities_schema,
        )
        validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate(
            {
                "$schema": "https://bib.rero.ch/schemas/remote_entities/remote_entity-v0.0.1.json",
                "viaf_pid": "56597999",
                "sources": ["rero", "gnd"],
            },
            remote_entities_schema,
        )
        validate(entity_person_data_tmp, remote_entities_schema)

    with pytest.raises(ValidationError):
        validate(
            {
                "$schema": "https://bib.rero.ch/schemas/remote_entities/remote_entity-v0.0.1.json",
                "pid": "ent_pers",
                "viaf_pid": "56597999",
            },
            remote_entities_schema,
        )
        validate(entity_person_data_tmp, remote_entities_schema)
