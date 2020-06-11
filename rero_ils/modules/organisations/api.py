# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""API for manipulating organisation."""


from functools import partial

from .models import OrganisationIdentifier, OrganisationMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..item_types.api import ItemTypesSearch
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


class OrganisationsSearch(IlsRecordsSearch):
    """Organisation search."""

    class Meta():
        """Meta class."""

        index = 'organisations'
        doc_types = None


class Organisation(IlsRecord):
    """Organisation class."""

    minter = organisation_id_minter
    fetcher = organisation_id_fetcher
    provider = OrganisationProvider
    model_cls = OrganisationMetadata

    def get_libraries_pids(self):
        """Get all libraries pids related to the organisation."""
        results = LibrariesSearch().source(['pid'])\
            .filter('term', organisation__pid=self.pid)\
            .scan()
        for result in results:
            yield result.pid

    def get_libraries(self):
        """Get all libraries related to the organisation."""
        pids = self.get_libraries_pids()
        for pid in pids:
            yield Library.get_record_by_pid(pid)

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

    @classmethod
    def get_all(cls):
        """Get all organisations."""
        return sorted([
            Organisation.get_record_by_id(_id)
            for _id in Organisation.get_all_ids()
        ], key=lambda org: org.get('name'))

    @classmethod
    def all_code(cls):
        """Get all code."""
        return [org.get('code') for org in cls.get_all()]

    @classmethod
    def get_record_by_viewcode(cls, viewcode):
        """Get record by view code."""
        result = OrganisationsSearch().filter(
            'term',
            code=viewcode
        ).execute()
        if result['hits']['total'] != 1:
            raise Exception(
                'Organisation (get_record_by_viewcode): Result not found.')

        return result['hits']['hits'][0]['_source']

    @property
    def organisation_pid(self):
        """Get organisation pid ."""
        return self.pid

    def online_circulation_category(self):
        """Get the default circulation category for online resources."""
        results = ItemTypesSearch().filter(
            'term', organisation__pid=self.pid).filter(
                'term', type='online').source(['pid']).scan()
        try:
            return next(results).pid
        except StopIteration:
            return None

    @classmethod
    def get_record_by_online_harvested_source(cls, source):
        """Get record by online harvested source."""
        results = OrganisationsSearch().filter(
            'term', online_harvested_source=source).scan()
        try:
            return Organisation.get_record_by_pid(next(results).pid)
        except StopIteration:
            return None

    def get_online_locations(self):
        """Get list of online locations."""
        return [library.online_location
                for library in self.get_libraries() if library.online_location]


class OrganisationsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Organisation

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(OrganisationsIndexer, self).bulk_index(record_id_iterator,
                                                     doc_type='org')
