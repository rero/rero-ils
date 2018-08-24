# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""organisation JSON schema tests."""

from __future__ import absolute_import, print_function

import pytest
from jsonschema import validate
from jsonschema.exceptions import ValidationError


def test_required(organisation_schema, minimal_organisation_record):
    """Test required for organisation jsonschema."""
    validate(minimal_organisation_record, organisation_schema)

    with pytest.raises(ValidationError):
        validate({}, organisation_schema)
        validate(minimal_organisation_record, organisation_schema)


def test_pid(organisation_schema, minimal_organisation_record):
    """Test pid for organisation jsonschema."""
    validate(minimal_organisation_record, organisation_schema)

    with pytest.raises(ValidationError):
        minimal_organisation_record['pid'] = 25
        validate(minimal_organisation_record, organisation_schema)


def test_name(organisation_schema, minimal_organisation_record):
    """Test name for organisation jsonschema."""
    validate(minimal_organisation_record, organisation_schema)

    with pytest.raises(ValidationError):
        minimal_organisation_record['name'] = 25
        validate(minimal_organisation_record, organisation_schema)


def test_address(organisation_schema,
                 minimal_organisation_record):
    """Test address for organisation jsonschema."""
    validate(minimal_organisation_record, organisation_schema)

    with pytest.raises(ValidationError):
        minimal_organisation_record['address'] = 25
        validate(minimal_organisation_record, organisation_schema)
