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

"""Other location Record tests.

   Some tests cannot be added in other files for several reason such as
   scope level fixtures.
"""

from rero_ils.modules.locations.api import Location, LocationsSearch


def test_location_get_all_pickup_locations(
        patron_martigny_no_email, loc_public_martigny, loc_public_sion):
    """Test pickup locations retrieval."""
    locations = Location.get_pickup_location_pids()
    assert set(locations) == {loc_public_martigny.pid, loc_public_sion.pid}

    locations = Location.get_pickup_location_pids(patron_martigny_no_email.pid)
    assert set(locations) == {loc_public_martigny.pid}
