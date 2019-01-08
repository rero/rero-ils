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

"""patron JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(item_type_schema, item_type_data_tmp):
    """Test required for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        validate({}, item_type_schema)
        validate(item_type_data_tmp, item_type_schema)


def test_pid(item_type_schema, item_type_data_tmp):
    """Test pid for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp['pid'] = 25
        validate(item_type_data_tmp, item_type_schema)


def test_name(item_type_schema, item_type_data_tmp):
    """Test name for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp['name'] = 25
        validate(item_type_data_tmp, item_type_schema)


def test_description(item_type_schema, item_type_data_tmp):
    """Test description for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp['description'] = 25
        validate(item_type_data_tmp, item_type_schema)


def test_organisation_pid(item_type_schema, item_type_data_tmp):
    """Test organisation_pid for item type jsonschemas."""
    validate(item_type_data_tmp, item_type_schema)

    with pytest.raises(ValidationError):
        item_type_data_tmp['organisation_pid'] = 25
        validate(item_type_data_tmp, item_type_schema)
