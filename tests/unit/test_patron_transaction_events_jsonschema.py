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

"""Patron transaction event JSON schema tests."""

from __future__ import absolute_import, print_function

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_patron_transaction_events_required(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test required for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        validate({}, patron_transaction_event_schema)


def test_patron_transaction_events_pid(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test pid for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["pid"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_note(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test note for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["note"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_type(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test type for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["type"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_subtype(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test subtype for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["subtype"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_operator(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test operator for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["operator"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_library(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test library for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["library"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_creation_date(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test creation_date for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["creation_date"] = 25
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_events_amount(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
    """Test amount for patron transaction event jsonschemas."""
    validate(
        patron_transaction_overdue_event_saxon_data, patron_transaction_event_schema
    )

    with pytest.raises(ValidationError):
        data = copy.deepcopy(patron_transaction_overdue_event_saxon_data)
        data["amount"] = "25"
        validate(data, patron_transaction_event_schema)


def test_patron_transaction_steps(
    patron_transaction_event_schema, patron_transaction_overdue_event_saxon_data
):
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
