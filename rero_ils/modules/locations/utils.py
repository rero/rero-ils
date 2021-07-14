# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Utilities for locations."""


def default_pickup_location_sort(item, pickup_locations):
    """Sort pickup location by default by name.

    :param item: the requested item.
    :param pickup_locations: the pickup locations to sort.
    """
    return sorted(
        list(filter(None, pickup_locations)),
        key=lambda loc: loc.get('pickup_name', loc.get('code'))
    )


def sort_pickup_locations_item_location_first(item, pickup_locations):
    """Sort pickup location by name with item location at first position.

    :param item: the requested item.
    :param pickup_locations: the pickup locations to sort.
    """
    pickup_locations = pickup_locations or []
    # first sort by name
    pickup_locations = sorted(
        list(filter(None, pickup_locations)),
        key=lambda loc: loc.get('pickup_name', loc.get('code'))
    )
    # place item location at top of the list
    item_loc_pid = item.location_pid
    item_pickup_location = next(
        (loc for loc in pickup_locations if loc.pid == item_loc_pid),
        None
    )
    if item_pickup_location:
        cleaned_pickup_location = [loc for loc in pickup_locations
                                   if loc.pid != item_pickup_location.pid]
        pickup_locations = [item_pickup_location] + cleaned_pickup_location
    return pickup_locations
