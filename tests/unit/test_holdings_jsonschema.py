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


"""Holdings JSON schema tests."""


from __future__ import absolute_import, print_function

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(holding_schema, holding_lib_martigny_w_patterns_data):
    """Test required for library jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        validate({}, holding_schema)
        validate(
            holding_lib_martigny_w_patterns_data, holding_schema)


def test_pid(
        holding_schema, holding_lib_martigny_w_patterns_data):
    """Test pid for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['pid'] = 25
        validate(data, holding_schema)


def test_call_number(holding_schema,
                     holding_lib_martigny_w_patterns_data):
    """Test call_number for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['call_number'] = 25
        validate(data, holding_schema)


def test_document(holding_schema,
                  holding_lib_martigny_w_patterns_data):
    """Test document for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['document'] = 25
        validate(data, holding_schema)


def test_circulation_category(
        holding_schema, holding_lib_martigny_w_patterns_data):
    """Test circulation_category for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['circulation_category'] = 25
        validate(data, holding_schema)


def test_location(
        holding_schema, holding_lib_martigny_w_patterns_data):
    """Test location for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['location'] = 25
        validate(data, holding_schema)


def test_holdings_type(
        holding_schema, holding_lib_martigny_w_patterns_data):
    """Test holdings_type for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['holdings_type'] = 1
        validate(data, holding_schema)


def test_patterns(
        holding_schema, holding_lib_martigny_w_patterns_data):
    """Test patterns for holding jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(holding_lib_martigny_w_patterns_data)
        data['patterns'] = 25
        validate(data, holding_schema)
