# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
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

"""organisation JSON schema tests."""

from __future__ import absolute_import, print_function

import copy

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(library_schema, library_data):
    """Test required for library jsonschemas."""
    validate(library_data, library_schema)

    with pytest.raises(ValidationError):
        validate({}, library_schema)
        validate(library_data, library_schema)


def test_pid(library_schema, library_data):
    """Test pid for library jsonschemas."""
    validate(library_data, library_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(library_data)
        data['pid'] = 25
        validate(data, library_schema)


def test_name(library_schema, library_data):
    """Test name for library jsonschemas."""
    validate(library_data, library_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(library_data)
        data['name'] = 25
        validate(data, library_schema)


def test_address(library_schema, library_data):
    """Test address for organisation jsonschemas."""
    validate(library_data, library_schema)

    with pytest.raises(ValidationError):
        data = copy.deepcopy(library_data)
        data['address'] = 25
        validate(data, library_schema)
