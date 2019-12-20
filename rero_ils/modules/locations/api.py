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

"""API for manipulating locations."""

from functools import partial

from flask_babelex import gettext as _

from .models import LocationIdentifier, LocationMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
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


class LocationsSearch(IlsRecordsSearch):
    """RecordsSearch for locations."""

    class Meta:
        """Search only on locations index."""

        index = 'locations'
        doc_types = None


class Location(IlsRecord):
    """Location class."""

    minter = location_id_minter
    fetcher = location_id_fetcher
    provider = LocationProvider
    model_cls = LocationMetadata
    pids_exist_check = {
        'required': {
            'lib': 'library'
        }
    }

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to allow only one location with field
        is_online = True per library. Also check that "pickup_name" field
        is present and not empty if location is pickup
        """
        online_location_pid = self.get_library().online_location
        if self.get('is_online') and online_location_pid and \
                self.pid != online_location_pid:
            return _('Another online location exists in this library')
        if self.get('is_pickup', False) and \
                not self.get('pickup_name', '').strip():
            return _('Pickup name field is required.')
        return True

    @classmethod
    def get_pickup_location_pids(cls, patron_pid=None, item_pid=None):
        """Return pickup locations."""
        from ..patrons.api import Patron
        from ..items.api import Item
        search = LocationsSearch()

        if item_pid:
            loc = Item.get_record_by_pid(item_pid).get_location()
            if loc.restrict_pickup_to:
                search = search.filter('terms', pid=loc.restrict_pickup_to)

        search = search.filter('term', is_pickup=True)

        if patron_pid:
            org_pid = Patron.get_record_by_pid(patron_pid).organisation_pid
            search = search.filter('term', organisation__pid=org_pid)

        locations = search.source(['pid']).scan()
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

    @property
    def library_pid(self):
        """Get library pid for location."""
        return self.replace_refs()['library']['pid']

    @property
    def organisation_pid(self):
        """Get organisation pid for location."""
        from ..libraries.api import Library

        library = Library.get_record_by_pid(self.library_pid)
        return library.organisation_pid

    @property
    def restrict_pickup_to(self):
        """Get restriction pickup location pid of location."""
        return [
            location['pid']
            for location in self.replace_refs().get('restrict_pickup_to', [])
        ]

    @classmethod
    def allow_request(cls, item, **kwargs):
        """Check if an item can be requested regarding its location.

        :param item : the item to check
        :param kwargs : addition arguments
        :return a tuple with True|False and reasons to disallow if False.
        """
        if item and not item.get_location().get('allow_request', False):
            return False, ["Item location disallows request."]
        return True, []


class LocationsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Location
