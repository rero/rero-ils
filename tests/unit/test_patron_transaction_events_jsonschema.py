# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction event JSON schema tests."""

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_patron_transaction_events_required(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test required for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        validate({}, patron_transaction_event_schema)


def test_patron_transaction_events_pid(patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data):
    """Test pid for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["pid"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_note(patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data):
    """Test note for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["note"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_type(patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data):
    """Test type for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["type"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_subtype(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test subtype for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["subtype"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_operator(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test operator for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["operator"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_library(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test library for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["library"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_creation_date(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test creation_date for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["creation_date"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_amount(patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data):
    """Test amount for patron transaction event jsonschemas."""
    validate(patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["amount"] = "25"
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_steps(patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data):
    """Test amount for patron transaction event jsonschemas."""

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["steps"] = []
        validate(data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["steps"] = [{"timestamp": "2020-12-31", "amount": "2"}]
        validate(data, patron_transaction_event_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["steps"] = [{"dummy": "2020-12-31", "amount": 2}]
        validate(data, patron_transaction_event_schema)
