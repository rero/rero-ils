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

"""Organisation with Libraries module tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_records.models import RecordMetadata

from rero_ils.modules.libraries_locations.api import LibraryWithLocations
from rero_ils.modules.libraries_locations.models import \
    LibrariesLocationsMetadata
from rero_ils.modules.locations.api import Location


def test_libraries_locations_create(
    db, minimal_library_record, minimal_location_record
):
    """Test organisation with libraries creation."""
    lib = LibraryWithLocations.create(minimal_library_record)
    loc = Record.create(minimal_location_record)
    assert lib.locations == []

    lib.add_location(loc)
    lib.dbcommit()
    assert lib.locations[0] == loc

    dump = lib.dumps()
    assert dump['locations'][0] == loc.dumps()


def test_delete_location(app, minimal_library_record, minimal_location_record):
    """Test LibrariesLocations delete."""
    lib = LibraryWithLocations.create(minimal_library_record, dbcommit=True)
    location = Location.create(minimal_location_record, dbcommit=True)
    lib.add_location(location, dbcommit=True)
    pid = PersistentIdentifier.get_by_object('loc', 'rec', location.id)
    assert pid.is_registered()
    lib.remove_location(location)
    assert pid.is_deleted()
    assert lib.locations == []

    location1 = Location.create(minimal_location_record, dbcommit=True)
    lib.add_location(location1, dbcommit=True)
    location2 = Location.create(minimal_location_record, dbcommit=True)
    lib.add_location(location2, dbcommit=True)
    location3 = Location.create(minimal_location_record, dbcommit=True)
    lib.add_location(location3, dbcommit=True)
    lib.remove_location(location2)
    assert len(lib.locations) == 2
    assert lib.locations[0]['pid'] == '2'
    assert lib.locations[1]['pid'] == '4'


def test_delete_library(app, minimal_library_record, minimal_location_record):
    """Test Library delete."""
    lib_count = LibrariesLocationsMetadata.query.count()
    rec_count = RecordMetadata.query.count()
    lib = LibraryWithLocations.create(minimal_library_record)
    location1 = Location.create(minimal_location_record)
    lib.add_location(location1)
    pid1 = PersistentIdentifier.get_by_object('loc', 'rec', location1.id)
    location2 = Location.create(minimal_location_record)
    lib.add_location(location2)
    pid2 = PersistentIdentifier.get_by_object('loc', 'rec', location2.id)
    location3 = Location.create(minimal_location_record)
    lib.add_location(location3)
    pid3 = PersistentIdentifier.get_by_object('loc', 'rec', location3.id)
    lib.dbcommit()
    assert LibrariesLocationsMetadata.query.count() == lib_count + 3
    assert RecordMetadata.query.count() == rec_count + 4
    assert pid1.is_registered()
    assert pid2.is_registered()
    assert pid3.is_registered()
    lib.delete(force=True)
    assert LibrariesLocationsMetadata.query.count() == lib_count
    assert RecordMetadata.query.count() == rec_count
    assert pid1.is_deleted()
    assert pid2.is_deleted()
    assert pid3.is_deleted()
