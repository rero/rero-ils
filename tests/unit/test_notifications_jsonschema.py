# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
