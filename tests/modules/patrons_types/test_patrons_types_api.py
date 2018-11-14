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

"""API tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.libraries_locations.api import LibraryWithLocations
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons_types.api import PatronType, PatronTypeSearch
from rero_ils.utils_test import es_flush_and_refresh


def test_patron_type_search():
    """Validate index name."""
    assert 'patrons_types' == PatronTypeSearch.Meta.index


def test_can_delete(
    app,
    limited_patron_type_record,
    limited_patron_simonetta,
    limited_library_record,
    limited_location_record,
    limited_patron_type_record_2,
    es_clear
):
    """Can Delete."""

    patron_type = PatronType.create(
        limited_patron_type_record,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    patron_type_2 = PatronType.create(
        limited_patron_type_record_2,
        dbcommit=True,
        reindex=True,
        delete_pid=False,
    )
    library = LibraryWithLocations.create(
        limited_library_record, dbcommit=True, reindex=True, delete_pid=False
    )
    location = Location.create(
        limited_location_record, dbcommit=True, reindex=True, delete_pid=False
    )
    library.add_location(location, dbcommit=True, reindex=True)
    simonetta = Patron.create(
        limited_patron_simonetta, dbcommit=True, reindex=True, delete_pid=False
    )

    assert patron_type.can_delete

    simonetta['patron_type_pid'] = patron_type_2['pid']
    simonetta.update(simonetta, dbcommit=True, reindex=True)
    es_flush_and_refresh()
    assert patron_type.can_delete


def test_exist_name_and_organisation_pid(app, minimal_patron_type_record):
    """Test for exist name and organisation pid."""
    patron_type = PatronType.create(
        minimal_patron_type_record, dbcommit=True, reindex=True
    )
    es_flush_and_refresh()

    result = PatronType.exist_name_and_organisation_pid(
        patron_type.get('name'), patron_type.get('organisation_pid')
    )
    assert result

    result = PatronType.exist_name_and_organisation_pid('NEW NAME', '1')
    assert result is None
