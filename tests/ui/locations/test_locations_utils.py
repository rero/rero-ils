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

from rero_ils.modules.locations.api import Location
from rero_ils.modules.locations.utils import default_pickup_location_sort, \
    sort_pickup_locations_item_location_first


def test_location_get_all_pickup_locations(
        patron_martigny, loc_public_martigny, loc_public_sion):
    """Test pickup locations retrieval."""
    locations = Location.get_pickup_location_pids()
    assert set(locations) == {loc_public_martigny.pid, loc_public_sion.pid}

    locations = Location.get_pickup_location_pids(patron_martigny.pid)
    assert set(locations) == {loc_public_martigny.pid}


def test_sort_pickup_locations(locations, item_lib_martigny):
    """Test sorting methods for pickup locations"""
    item = item_lib_martigny
    pickups_locations = [
        Location.get_record_by_pid(pid)
        for pid in Location.get_pickup_location_pids()
    ]

    sorted_locations = default_pickup_location_sort(item, pickups_locations)
    assert sorted_locations[0].pid == 'loc5'

    sorted_locations = sort_pickup_locations_item_location_first(
        item, pickups_locations)
    assert sorted_locations[0].pid == 'loc1'
    assert sorted_locations[1].pid == 'loc5'
