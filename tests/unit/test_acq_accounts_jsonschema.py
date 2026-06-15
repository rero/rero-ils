# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquistion accounts JSON schema tests."""

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
