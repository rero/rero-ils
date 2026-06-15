# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_patron_transactions_required(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test required for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_transaction_schema)


def test_patron_transactions_pid(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test pid for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["pid"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_note(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test note for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["note"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_status(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test status for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["status"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_type(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test type for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["type"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_patron(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test patron for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["patron"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_notification(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test notification for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["notification"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_organisation(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test organisation for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["organisation"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_creation_date(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test creation_date for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["creation_date"] = 25
        validate(data, patron_transaction_schema)


def test_patron_transactions_total_amount(patron_transaction_schema, patron_transaction_overdue_saxon_data):
    """Test total_amount for patron transaction jsonschemas."""
    validate(patron_transaction_overdue_saxon_data, patron_transaction_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_saxon_data)
        data["total_amount"] = "25"
        validate(data, patron_transaction_schema)
