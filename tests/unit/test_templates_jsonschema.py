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

"""Templates JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(template_schema, templ_doc_public_martigny_data_tmp):
    """Test required for template jsonschema."""
    validate(templ_doc_public_martigny_data_tmp, template_schema)

    with pytest.raises(ValidationError):
        validate({}, template_schema)
        validate(templ_doc_public_martigny_data_tmp, template_schema)


def test_template_all_jsonschema_keys_values(
    template_schema, templ_doc_public_martigny_data_tmp
):
    """Test all keys and values for template jsonschema."""
    record = templ_doc_public_martigny_data_tmp
    validate(record, template_schema)
    validator = [
        {"key": "pid", "value": 25},
        {"key": "name", "value": 25},
        {"key": "description", "value": 25},
        {"key": "organistion", "value": 25},
        {"key": "template_type", "value": 25},
        {"key": "creator", "value": 25},
        {"key": "visibility", "value": 25},
        {"key": "data", "value": 25},
    ]
    for element in validator:
        with pytest.raises(ValidationError):
            record[element["key"]] = element["value"]
            validate(record, template_schema)
