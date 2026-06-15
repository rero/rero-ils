# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Notifications JSON schema tests."""

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from rero_ils.modules.notifications.api import Notification


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
        dummy_notification["pid"] = 25
        validate(dummy_notification, notification_schema)


def test_notification_type(notification_schema, dummy_notification):
    """Test type for notification jsonschemas."""
    validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        dummy_notification["notification_type"] = 25
        validate(dummy_notification, notification_schema)


def test_loan(app, notification_schema, dummy_notification):
    """Test loan for notification jsonschemas."""
    validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        dummy_notification["context"]["loan"] = 25
        validate(dummy_notification, notification_schema)

    with pytest.raises(ValidationError):
        notif = Notification(dummy_notification)
        del notif["context"]["loan"]
        notif.validate()
