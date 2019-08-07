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

"""API for manipulating organisation."""


from functools import partial

from .models import OrganisationIdentifier
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..libraries.api import LibrariesSearch, Library
from ..minters import id_minter
from ..providers import Provider

# provider
OrganisationProvider = type(
    'OrganisationProvider',
    (Provider,),
    dict(identifier=OrganisationIdentifier, pid_type='org')
)
# minter
organisation_id_minter = partial(id_minter, provider=OrganisationProvider)
# fetcher
organisation_id_fetcher = partial(id_fetcher, provider=OrganisationProvider)


class Organisation(IlsRecord):
    """Organisation class."""

    minter = organisation_id_minter
    fetcher = organisation_id_fetcher
    provider = OrganisationProvider

    def get_libraries(self):
        """Get all libraries related to the organisation."""
        results = LibrariesSearch().source(['pid'])\
            .filter('term', organisation__pid=self.pid)\
            .scan()
        for library in results:
            yield Library.get_record_by_pid(library.pid)

    def get_number_of_libraries(self):
        """Get number of libraries."""
        results = LibrariesSearch().filter(
            'term', organisation__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        libraries = self.get_number_of_libraries()
        if libraries:
            links['libraries'] = libraries
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    @property
    def organisation_pid(self):
        """Get organisation pid ."""
        return self.pid
