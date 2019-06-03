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

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(notification_schema, notification_martigny_data_tmp):
    """Test required for notification jsonschemas."""
    validate(notification_martigny_data_tmp, notification_schema)

    with pytest.raises(ValidationError):
        validate({}, notification_schema)
        validate(notification_martigny_data_tmp, notification_schema)


def test_pid(notification_schema, notification_martigny_data_tmp):
    """Test pid for notification jsonschemas."""
    validate(notification_martigny_data_tmp, notification_schema)

    with pytest.raises(ValidationError):
        notification_martigny_data_tmp['pid'] = 25
        validate(notification_martigny_data_tmp, notification_schema)


def test_notification_type(
        notification_schema, notification_martigny_data_tmp):
    """Test type for notification jsonschemas."""
    validate(notification_martigny_data_tmp, notification_schema)

    with pytest.raises(ValidationError):
        notification_martigny_data_tmp['notification_type'] = 25
        validate(notification_martigny_data_tmp, notification_schema)


def test_patron(notification_schema, notification_martigny_data_tmp):
    """Test patron for notification jsonschemas."""
    validate(notification_martigny_data_tmp, notification_schema)

    with pytest.raises(ValidationError):
        notification_martigny_data_tmp['patron'] = 25
        validate(notification_martigny_data_tmp, notification_schema)


def test_transaction_location(
        notification_schema, notification_martigny_data_tmp):
    """Test transaction location for notification jsonschemas."""
    validate(notification_martigny_data_tmp, notification_schema)

    with pytest.raises(ValidationError):
        notification_martigny_data_tmp['transaction_location'] = 25
        validate(notification_martigny_data_tmp, notification_schema)
