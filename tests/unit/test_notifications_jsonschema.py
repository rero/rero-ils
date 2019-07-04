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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Notifications JSON schema tests."""


import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(notification_schema, dummy_notification):
    """Test required for notification jsonschemas."""
    validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        validate({}, notification_schema)
        validate(dummy_notification, notification_schema)


def test_pid(notification_schema, dummy_notification):
    """Test pid for notification jsonschemas."""
    validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        dummy_notification['pid'] = 25
        validate(dummy_notification, notification_schema)


def test_notification_type(
        notification_schema, dummy_notification):
    """Test type for notification jsonschemas."""
    validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        dummy_notification['notification_type'] = 25
        validate(dummy_notification, notification_schema)


def test_loan(notification_schema, dummy_notification):
    """Test loan for notification jsonschemas."""
    validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        dummy_notification['loan'] = 25
        validate(dummy_notification, notification_schema)
