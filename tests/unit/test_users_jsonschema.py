# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""User JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(user_schema, user_data_tmp):
    """Test required for user jsonschemas."""
    validate(user_data_tmp, user_schema)

    with pytest.raises(ValidationError):
        validate({}, user_schema)


def test_user_all_jsonschema_keys_values(
        user_schema, user_data_tmp):
    """Test all keys and values for user jsonschema."""
    record = user_data_tmp
    validate(record, user_schema)
    validator = [
        {'key': 'first_name', 'value': 25},
        {'key': 'last_name', 'value': 25},
        {'key': 'birth_date', 'value': 25},
        {'key': 'gender', 'value': 25},
        {'key': 'street', 'value': 25},
        {'key': 'postal_code', 'value': 25},
        {'key': 'city', 'value': 25},
        {'key': 'country', 'value': 25},
        {'key': 'mobile_phone', 'value': 25},
        {'key': 'business_phone', 'value': 25},
        {'key': 'mobile_phone', 'value': 25},
        {'key': 'other_phone', 'value': 25},
        {'key': 'keep_history', 'value': 25},
        {'key': 'user_id', 'value': '25'}
    ]
    for element in validator:
        with pytest.raises(ValidationError):
            record[element['key']] = element['value']
            validate(record, user_schema)
