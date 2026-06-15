# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquistion accounts JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(budget_schema, budget_2020_martigny_data_tmp):
    """Test required for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        validate({}, budget_schema)
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_pid(budget_schema, budget_2020_martigny_data_tmp):
    """Test pid for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["pid"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_name(budget_schema, budget_2020_martigny_data_tmp):
    """Test name for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["name"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_organisation_pid(budget_schema, budget_2020_martigny_data_tmp):
    """Test organisation_pid for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["organisation_pid"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_library(budget_schema, budget_2020_martigny_data_tmp):
    """Test library for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["library"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_start_date(budget_schema, budget_2020_martigny_data_tmp):
    """Test start date for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["start_date"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_end_date(budget_schema, budget_2020_martigny_data_tmp):
    """Test end date for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["end_date"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)


def test_is_active(budget_schema, budget_2020_martigny_data_tmp):
    """Test is_active te for budgets jsonschemas."""
    validate(budget_2020_martigny_data_tmp, budget_schema)

    with pytest.raises(ValidationError):
        budget_2020_martigny_data_tmp["is_active"] = 25
        validate(budget_2020_martigny_data_tmp, budget_schema)
