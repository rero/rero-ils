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

"""Location JSON schema tests."""

from __future__ import absolute_import, print_function

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_locations_required(location_schema, loc_public_martigny_data):
    """Test required for location jsonschemas."""
    validate(loc_public_martigny_data, location_schema)

    with pytest.raises(ValidationError):
        validate({}, location_schema)


def test_locations_pid(location_schema, loc_public_martigny_data):
    """Test pid for location jsonschemas."""
    validate(loc_public_martigny_data, location_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(loc_public_martigny_data)
        data['pid'] = 25
        validate(data, location_schema)


def test_locations_name(location_schema, loc_public_martigny_data):
    """Test name for location jsonschemas."""
    validate(loc_public_martigny_data, location_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(loc_public_martigny_data)
        data['name'] = 25
        validate(data, location_schema)
