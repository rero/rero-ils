# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Tasks related to `Location` resources."""

from celery import shared_task

from rero_ils.modules.utils import extracted_data_from_ref


@shared_task(ignore_result=True)
def remove_location_from_restriction(restricted_location):
    """Remove a location from pickup restriction for other locations.

    :param restricted_location: the location record to remove.
    :type: dict
    """
    from .api import Location, LocationsSearch

    # If the location is defined as a pickup location, no need to remove it
    # from restriction; just stop the process.
    if restricted_location.get('is_pickup', False):
        return

    # Search for locations that uses the restricted location into
    # `restrict_pickup_to` field. For each of these locations, remove the
    # restricted location from this field and reindex the record.
    restricted_pid = restricted_location['pid']
    query = LocationsSearch() \
        .filter('term', restrict_pickup_to__pid=restricted_pid) \
        .source(False)
    for hit in query.scan():
        location = Location.get_record(hit.meta.id)
        restricted_location = [
            location_ref
            for location_ref in location['restrict_pickup_to']
            if extracted_data_from_ref(location_ref) != restricted_pid
        ]
        del location['restrict_pickup_to']
        if restricted_location:
            location['restrict_pickup_to'] = restricted_location
        location.update(location, dbcommit=True, reindex=True)
