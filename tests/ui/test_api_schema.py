# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.theme.views import replace_ref_url


def test_replace_refs(app):
    """Test replace $refs in schema."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "TEST SCHEMA",
        "type": "object",
        "required": [
            "$schema",
            "pid",
            "test1",
            "test2"
        ],
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
                "default": "https://bib.rero.ch/schemas/tests/test.json"
            },
            "pid": {
                "title": "Document PID",
                "type": "string",
                "minLength": 1
            },
            "test1": {
                "$ref": "https://bib.rero.ch/schemas/tests/test1.json#/1"
            },
            "test2": {
                "$ref": "https://bib.rero.ch/schemas/tests/test2.json#/2"
            }
        }
    }
    schema = replace_ref_url(schema, 'test.org')
    assert schema['properties']['test1']['$ref'] == \
        'https://test.org/schemas/tests/test1.json#/1'
    assert schema['properties']['test2']['$ref'] == \
        'https://test.org/schemas/tests/test2.json#/2'
