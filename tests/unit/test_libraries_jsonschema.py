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

"""Libraries JSON schema tests."""

from __future__ import absolute_import, print_function

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(library_schema, lib_martigny_data):
    """Test required for library jsonschemas."""
    validate(lib_martigny_data, library_schema)

    with pytest.raises(ValidationError):
        validate({}, library_schema)
        validate(lib_martigny_data, library_schema)


def test_pid(library_schema, lib_martigny_data):
    """Test pid for library jsonschemas."""
    validate(lib_martigny_data, library_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(lib_martigny_data)
        data['pid'] = 25
        validate(data, library_schema)


def test_name(library_schema, lib_martigny_data):
    """Test name for library jsonschemas."""
    validate(lib_martigny_data, library_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(lib_martigny_data)
        data['name'] = 25
        validate(data, library_schema)


def test_address(library_schema, lib_martigny_data):
    """Test address for library jsonschemas."""
    validate(lib_martigny_data, library_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(lib_martigny_data)
        data['address'] = 25
        validate(data, library_schema)
