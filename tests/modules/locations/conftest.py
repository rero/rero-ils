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

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import shutil
import tempfile
from json import loads

import pytest
from pkg_resources import resource_string


@pytest.yield_fixture()
def minimal_location_record():
    """Simple location record."""
    yield {
        '$schema': 'http://ils.test.rero.ch/schema\
            /locations/location-v0.0.1.json',
        'pid': '1',
        'code': 'net2-store-base',
        'name': 'Store Base'
    }


@pytest.fixture()
def location_schema():
    """Location Jsonschema for records."""
    schema_in_bytes = resource_string(
        'reroils_app.modules.locations.jsonschemas',
        'locations/location-v0.0.1.json')
    schema = loads(schema_in_bytes.decode('utf8'))
    return schema


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)
