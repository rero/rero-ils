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

"""organisation JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(organisation_schema, org_martigny_data):
    """Test required for organisation jsonschemas."""
    validate(org_martigny_data, organisation_schema)

    with pytest.raises(ValidationError):
        validate({}, organisation_schema)
        validate(org_martigny_data, organisation_schema)


def test_pid(organisation_schema, org_martigny_data):
    """Test pid for organisation jsonschemas."""
    validate(org_martigny_data, organisation_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(org_martigny_data)
        data["pid"] = 25
        validate(data, organisation_schema)


def test_name(organisation_schema, org_martigny_data):
    """Test name for organisation jsonschemas."""
    validate(org_martigny_data, organisation_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(org_martigny_data)
        data["name"] = 25
        validate(data, organisation_schema)


def test_address(organisation_schema, org_martigny_data):
    """Test address for organisation jsonschemas."""
    validate(org_martigny_data, organisation_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(org_martigny_data)
        data["address"] = 25
        validate(data, organisation_schema)


def test_default_currency(organisation_schema, org_martigny_data):
    """Test default currency for organisation jsonschemas."""
    validate(org_martigny_data, organisation_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(org_martigny_data)
        data["default_currency"] = 25  # bad type
        validate(data, organisation_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(org_martigny_data)
        data["default_currency"] = "dummy"  # bad string length
        validate(data, organisation_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(org_martigny_data)
        data["default_currency"] = "chf"  # bad string case
        validate(data, organisation_schema)


def test_homepage_fields(organisation_schema, org_martigny_data):
    """Test homepage fields for organisation jsonschemas."""
    data = copy.deepcopy(org_martigny_data)
    data["homepage"] = {
        "slogan": [
            {"language": "fr", "value": "Bienvenue"},
            {"language": "en", "value": "Welcome"},
        ],
        "placeholder": [
            {"language": "fr", "value": "Que cherchez-vous?"},
            {"language": "en", "value": "What are you looking for?"},
        ],
        "blocks": {
            "left": [
                {"language": "fr", "value": "<h3>Bloc gauche</h3>"},
                {"language": "en", "value": "<h3>Left block</h3>"},
            ],
            "center": [{"language": "fr", "value": "<h3>Bloc centre</h3>"}],
            "right": [{"language": "fr", "value": "<h3>Bloc droite</h3>"}],
        },
    }

    validate(data, organisation_schema)


def test_homepage_block_label_type(organisation_schema, org_martigny_data):
    """Test homepage block label type for organisation jsonschemas."""
    data = copy.deepcopy(org_martigny_data)
    data["homepage"] = {"blocks": {"left": [{"language": "fr", "value": 25}]}}

    with pytest.raises(ValidationError):
        validate(data, organisation_schema)
