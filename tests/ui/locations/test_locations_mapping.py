# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries search index mapping tests."""

from rero_ils.modules.locations.api import Location, LocationsSearch
from tests.utils import get_mapping


def test_location_mapping(search, db, loc_public_martigny_data, lib_martigny, org_martigny):
    """Test library search index mapping."""
    search = LocationsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    loc = Location.create(loc_public_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    new_mapping = get_mapping(search.Meta.index)
    assert mapping == new_mapping
    loc.delete(force=True, dbcommit=True, delindex=True)


def test_location_search_mapping(app, locations_records):
    """Test library search mapping."""
    search = LocationsSearch()

    c = search.query("match", code="MARTIGNY-PUBLIC").count()
    assert c == 1
    c = search.query("match", code="SAXON-PUBLIC").count()
    assert c == 1
