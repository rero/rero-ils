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

"""Acquistion accounts JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test required for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        validate({}, acq_account_schema)
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)


def test_pid(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test pid for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        acq_account_fiction_martigny_data_tmp["pid"] = 25
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)


def test_name(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test name for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        acq_account_fiction_martigny_data_tmp["name"] = 25
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)


def test_description(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test description for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        acq_account_fiction_martigny_data_tmp["description"] = 25
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)


def test_organisation_pid(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test organisation_pid for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        acq_account_fiction_martigny_data_tmp["organisation_pid"] = 25
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)


def test_budget(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test budget for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        acq_account_fiction_martigny_data_tmp["budget"] = 25
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)


def test_allocated_amount(acq_account_schema, acq_account_fiction_martigny_data_tmp):
    """Test allocated_amount for acq accounts jsonschemas."""
    validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)

    with pytest.raises(ValidationError):
        acq_account_fiction_martigny_data_tmp["allocated_amount"] = "test"
        validate(acq_account_fiction_martigny_data_tmp, acq_account_schema)
