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

from invenio_search.api import RecordsSearch

from .models import LocationIdentifier
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
LocationProvider = type(
    'LocationProvider',
    (Provider,),
    dict(identifier=LocationIdentifier, pid_type='loc')
)
# minter
location_id_minter = partial(id_minter, provider=LocationProvider)
# fetcher
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
    def get_pickup_location_pids(cls, patron_pid=None):
        """Return pickup locations."""
        # TODO: filter by patron libraries or organisations
        locations = LocationsSearch()\
            .filter('term', is_pickup=True)\
            .source(['pid']).scan()
        for location in locations:
            yield location.pid

    def get_library(self):
        """Get library."""
        from ..libraries.api import Library
        library_pid = self.replace_refs()['library']['pid']
        return Library.get_record_by_pid(library_pid)

    def get_number_of_items(self):
        """Get number of items."""
        from ..items.api import ItemsSearch
        results = ItemsSearch().filter(
            'term', location__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        items = self.get_number_of_items()
        if items:
            links['items'] = items
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete
