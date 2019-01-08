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

from functools import partial

from invenio_db import db
from invenio_records.models import RecordMetadata
from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from .providers import LocationProvider

# from sqlalchemy import JSONB


location_id_minter = partial(id_minter, provider=LocationProvider)

location_id_fetcher = partial(id_fetcher, provider=LocationProvider)


class LocationsSearch(RecordsSearch):
    """RecordsSearch for locations."""

    class Meta:
        """Search only on locations index."""

        index = 'locations'


class Location(IlsRecord):
    """Location class."""

    minter = location_id_minter
    fetcher = location_id_fetcher
    provider = LocationProvider

    @classmethod
    def get_all_pickup_locations(cls):
        """."""
        with db.session.no_autoflush:
            query = RecordMetadata.query
            # .filter(
            #     RecordMetadata.json['is_pickup'].cast(sqlalchemy.Boolean).is_(True)
            # )
            return [cls(obj.json, model=obj) for obj in query.all()]
        # return []
    # # TODO make global function
    # @classmethod
    # def get_all_pids(cls):
    #     """Get all location pids."""
    #     libraries_locations = LibrariesLocationsMetadata.query.all()

    #     locs_id = []

    #     for library_location in libraries_locations:
    #         loc_id = library_location.location_id
    #         pid = PersistentIdentifier.get_by_object('loc', 'rec', loc_id)
    #         locs_id.append(pid.pid_value)

    #     return locs_id

    # def get_all_items_pids(self):
    #     """Get all items pids."""
    #     items_with_location = (
    #         DocumentsSearch()
    #         .filter('term', **{'itemslist.location_pid': self.pid})
    #         .source(includes=['itemslist.pid'])
    #         .scan()
    #     )
    #     pids = []
    #     for document in items_with_location:
    #         for items in document['itemslist']:
    #             item = items.to_dict()
    #             pids.append(item.get('pid'))
    #     return sorted(pids, key=int)

    # @property
    # def can_delete(self):
    #     """Record can be deleted."""
    #     return len(self.get_all_items_pids()) == 0
