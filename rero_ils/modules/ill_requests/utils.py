# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

"""Utils methods for ILL requests."""

from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import current_patrons


def get_pickup_location_options():
    """Get all pickup location for all patron accounts."""
    for ptrn_pid in [ptrn.pid for ptrn in current_patrons]:
        for pid in Location.get_pickup_location_pids(ptrn_pid):
            location = Location.get_record_by_pid(pid)
            location_name = location.get('pickup_name', location.get('name'))
            yield tuple([location.pid, location_name])
