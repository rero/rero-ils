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

"""API for manipulating locations."""

from invenio_pidstore.models import PersistentIdentifier
from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..members_locations.models import MembersLocationsMetadata
from .fetchers import location_id_fetcher
from .minters import location_id_minter
from .providers import LocationProvider


class LocationsSearch(RecordsSearch):
    """RecordsSearch for borrowed documents."""

    class Meta:
        """Search only on documents index."""

        index = 'documents'


class Location(IlsRecord):
    """Location class."""

    minter = location_id_minter
    fetcher = location_id_fetcher
    provider = LocationProvider

    @classmethod
    def get_location(cls, pid):
        """Get location."""
        location = cls.get_record_by_pid(pid)
        return location, location

    # TODO make global function
    @classmethod
    def get_all_pids(cls):
        """Get all location pids."""
        members_locations = MembersLocationsMetadata.query.all()

        locs_id = []

        for member_location in members_locations:
            loc_id = member_location.location_id
            pid = PersistentIdentifier.get_by_object('loc', 'rec', loc_id)
            locs_id.append(pid.pid_value)

        return locs_id

    def get_all_items_pids(self):
        """Get all items pids."""
        items_with_location = LocationsSearch().filter(
            "term", **{"itemslist.location_pid": self.pid}
        ).source(includes=['itemslist.pid']).scan()
        pids = []
        for document in items_with_location:
            for items in document['itemslist']:
                item = items.to_dict()
                pids.append(item.get('pid'))
        return sorted(pids, key=int)

    @property
    def can_delete(self):
        """Record can be deleted."""
        return len(self.get_all_items_pids()) == 0
