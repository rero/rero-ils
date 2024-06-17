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


def test_required(holding_schema, holding_lib_martigny_data):
    """Test required for holdings of type standard jsonschemas."""
    validate(holding_lib_martigny_data, holding_schema)

    with pytest.raises(ValidationError):
        validate({}, holding_schema)
        validate(holding_lib_martigny_data, holding_schema)


def test_required_patterns(holding_schema, holding_lib_martigny_w_patterns_data):
    """Test required for holdings jsonschemas."""
    validate(holding_lib_martigny_w_patterns_data, holding_schema)

    with pytest.raises(ValidationError):
        validate({}, holding_schema)
        validate(holding_lib_martigny_w_patterns_data, holding_schema)


def test_required_patterns_frequency(
    holding_schema, holding_lib_martigny_w_patterns_data
):
    """Test required for frequency in the patterns."""
    holding = copy.deepcopy(holding_lib_martigny_w_patterns_data)
    del holding["patterns"]["frequency"]

    with pytest.raises(ValidationError):
        validate(holding, holding_schema)


def test_holdings_all_jsonschema_keys_values(
    holding_schema, holding_lib_martigny_w_patterns_data
):
    """Test all keys and values for holdings jsonschema."""
    record = holding_lib_martigny_w_patterns_data
    validate(record, holding_schema)
    validator = [
        {"key": "pid", "value": 25},
        {"key": "call_number", "value": 25},
        {"key": "second_call_number", "value": 25},
        {"key": "document", "value": 25},
        {"key": "circulation_category", "value": 25},
        {"key": "organisation", "value": 25},
        {"key": "library", "value": 25},
        {"key": "location", "value": 25},
        {"key": "holdings_type", "value": 25},
        {"key": "patterns", "value": 25},
        {"key": "enumerationAndChronology", "value": 25},
        {"key": "supplementaryContent", "value": 25},
        {"key": "index", "value": 25},
        {"key": "missing_issues", "value": 25},
        {"key": "notes", "value": 25},
        {"key": "vendor", "value": 25},
        {"key": "issue_binding", "value": 25},
        {"key": "acquisition_status", "value": 25},
        {"key": "acquisition_method", "value": 25},
        {"key": "acquisition_expected_end_date", "value": 25},
        {"key": "general_retention_policy", "value": 25},
        {"key": "completeness", "value": 25},
        {"key": "composite_copy_report", "value": 25},
        {"key": "_masked", "value": 25},
    ]
    for element in validator:
        with pytest.raises(ValidationError):
            record[element["key"]] = element["value"]
            validate(record, holding_schema)
