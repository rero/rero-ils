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

"""API for manipulating locations associated to a libraries."""


from ..api import RecordWithElements
from ..libraries.api import Library
from ..libraries.fetchers import library_id_fetcher
from ..libraries.minters import library_id_minter
from ..libraries.providers import LibraryProvider
from ..locations.api import Location
from .models import LibrariesLocationsMetadata


class LibraryWithLocations(RecordWithElements):
    """Api for Documents with Items."""

    record = Library
    element = Location
    metadata = LibrariesLocationsMetadata
    elements_list_name = 'locations'
    minter = library_id_minter
    fetcher = library_id_fetcher
    provider = LibraryProvider

    # @property
    # def elements(self):
    #     """Return an array of Locations."""
    #     if self.model is None:
    #         raise MissingModelError()
    #
    #     # retrive all libraries in the relation table
    #     # sorted by libraries creation date
    #     libraries_locations = self.metadata.query\
    #         .filter_by(library_id=self.id)\
    #         .join(self.metadata.location)\
    #         .order_by(RecordMetadata.created)
    #     to_return = []
    #     for lib_loc in libraries_locations:
    #         location = Location.get_record_by_id(lib_loc.location.id)
    #         to_return.append(location)
    #     return to_return

    @property
    def locations(self):
        """Locations."""
        return self.elements

    @property
    def pickup_locations(self):
        """Pickup Locations."""
        locations = []
        for location in self.elements:
            if location.get('is_pickup'):
                locations.append(location)
        return locations

    def add_location(self, location, dbcommit=False, reindex=False):
        """Add an location."""
        super(LibraryWithLocations, self).add_element(
            location,
            dbcommit=dbcommit,
            reindex=reindex
        )

    def remove_location(self, location, force=False, delindex=False):
        """Remove an location."""
        super(LibraryWithLocations, self).remove_element(
            location,
            force=force,
            delindex=delindex
        )

    @classmethod
    def get_library_by_locationid(cls, id_, with_deleted=False):
        """Retrieve the library by location id."""
        return super(LibraryWithLocations, cls).get_record_by_elementid(
            id_, with_deleted
        )

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(LibraryWithLocations, self).dumps(*kwargs)
        for item in data.get('itemslist', []):
            pid, location = Location.get_location(item.get('location_pid'))
            if location:
                item['location_name'] = location.get('name')
                library = Library.get_library_by_locationid(location.id)
                if library:
                    item['library_pid'] = library.pid
        return data
