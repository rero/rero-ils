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
from invenio_records.models import RecordMetadata

from rero_ils.modules.libraries_locations.api import LibraryWithLocations
from rero_ils.modules.organisations_libraries.api import \
    OrganisationWithLibraries
from rero_ils.modules.organisations_libraries.models import \
    OrganisationsLibrariesMetadata


def test_organisation_libraries_create(db, minimal_organisation_record,
                                       minimal_library_record):
    """Test organisation with libraries creation."""
    org = OrganisationWithLibraries.create(
        minimal_organisation_record,
        dbcommit=True
    )
    lib = LibraryWithLocations.create(minimal_library_record, dbcommit=True)
    assert org.libraries == []

    org.add_library(lib, dbcommit=True)
    assert org.libraries[0] == lib

    dump = org.dumps()
    assert dump['libraries'][0] == lib.dumps()


def test_delete_library(app,
                        minimal_organisation_record,
                        minimal_library_record):
    """Test OrganisationsLibraries delete."""
    org = OrganisationWithLibraries.create(
        minimal_organisation_record,
        dbcommit=True
    )
    library = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    org.add_library(library, dbcommit=True)
    pid = PersistentIdentifier.get_by_object('lib', 'rec', library.id)
    assert pid.is_registered()
    org.remove_library(library)
    assert pid.is_deleted()
    assert org.libraries == []

    library1 = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    org.add_library(library1, dbcommit=True)
    library2 = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    org.add_library(library2, dbcommit=True)
    library3 = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    org.add_library(library3, dbcommit=True)
    org.remove_library(library2)
    assert len(org.libraries) == 2
    assert org.libraries[0]['pid'] == '2'
    assert org.libraries[1]['pid'] == '4'


def test_delete_organisation(app,
                             minimal_organisation_record,
                             minimal_library_record):
    """Test Organisation delete."""
    org_count = OrganisationsLibrariesMetadata.query.count()
    rec_count = RecordMetadata.query.count()
    org = OrganisationWithLibraries.create(
        minimal_organisation_record,
        dbcommit=True
    )
    library1 = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    pid1 = PersistentIdentifier.get_by_object('lib', 'rec', library1.id)
    library2 = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    pid2 = PersistentIdentifier.get_by_object('lib', 'rec', library2.id)
    library3 = LibraryWithLocations.create(
        minimal_library_record,
        dbcommit=True
    )
    pid3 = PersistentIdentifier.get_by_object('lib', 'rec', library3.id)
    org.add_library(library1, dbcommit=True)
    org.add_library(library2, dbcommit=True)
    org.add_library(library3, dbcommit=True)
    assert OrganisationsLibrariesMetadata.query.count() == org_count + 3
    assert RecordMetadata.query.count() == rec_count + 4
    assert pid1.is_registered()
    assert pid2.is_registered()
    assert pid3.is_registered()
    org.delete(force=True)
    assert OrganisationsLibrariesMetadata.query.count() == org_count
    assert RecordMetadata.query.count() == rec_count
    assert pid1.is_deleted()
    assert pid2.is_deleted()
    assert pid3.is_deleted()
