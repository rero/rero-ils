# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""CircPolicy Record tests."""

from rero_ils.theme.views import replace_ref_url


def test_replace_refs(app):
    """Test replace $refs in schema."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "TEST SCHEMA",
        "type": "object",
        "required": ["$schema", "pid", "test1", "test2"],
        "propertiesOrder": [
            "pid",
            "test1",
            "test2",
        ],
        "additionalProperties": False,
        "properties": {
            "$schema": {
                "title": "Schema",
                "description": "Schema to validate document against.",
                "type": "string",
                "default": "https://bib.rero.ch/schemas/tests/test.json",
            },
            "pid": {"title": "Document PID", "type": "string", "minLength": 1},
            "test1": {"$ref": "https://bib.rero.ch/schemas/tests/test1.json#/1"},
            "test2": {"$ref": "https://bib.rero.ch/schemas/tests/test2.json#/2"},
        },
    }
    schema = replace_ref_url(schema, "test.org")
    assert schema["properties"]["test1"]["$ref"] == "https://test.org/schemas/tests/test1.json#/1"
    assert schema["properties"]["test2"]["$ref"] == "https://test.org/schemas/tests/test2.json#/2"
