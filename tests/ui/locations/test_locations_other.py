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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Other location Record tests.

   Some tests cannot be added in other files for several reason such as
   scope level fixtures.
"""

from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.locations.api import Location


def test_location_get_all_pickup_locations(
    patron_martigny, loc_public_martigny, loc_public_sion
):
    """Test pickup locations retrieval."""
    locations = Location.get_pickup_location_pids()
    assert set(locations) == {loc_public_martigny.pid, loc_public_sion.pid}

    locations = Location.get_pickup_location_pids(patron_martigny.pid)
    assert set(locations) == {loc_public_martigny.pid}


def test_location_get_links_to_me(
    loc_public_martigny, loc_public_sion, item_lib_martigny
):
    """Test pickup locations retrieval."""

    assert loc_public_martigny.get_links_to_me() == {"items": 1, "holdings": 1}
    assert loc_public_martigny.get_links_to_me(get_pids=True) == {
        "items": ["item1"],
        "holdings": ["1"],
    }

    assert loc_public_sion.get_links_to_me() == {}
    item_lib_martigny["temporary_location"] = {
        "$ref": f"https://bib.rero.ch/api/locations/{loc_public_sion.pid}"
    }
    item_lib_martigny.update(data=item_lib_martigny, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert loc_public_sion.get_links_to_me() == {"items": 1}
    assert loc_public_sion.get_links_to_me(get_pids=True) == {"items": ["item1"]}
