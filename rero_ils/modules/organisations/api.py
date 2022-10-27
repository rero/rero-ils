# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

from elasticsearch.exceptions import NotFoundError

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import sorted_pids
from rero_ils.modules.vendors.api import Vendor, VendorsSearch

from .models import OrganisationIdentifier, OrganisationMetadata

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

    class Meta:
        """Meta class."""

        index = 'organisations'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None

    def get_record_by_viewcode(self, viewcode, fields=None):
        """Search by viewcode."""
        query = self.filter('term', code=viewcode).extra(size=1)
        if fields:
            query = query.source(includes=fields)
        response = query.execute()
        if response.hits.total.value != 1:
            raise NotFoundError(
                f'Organisation viewcode {viewcode}: Result not found.')
        return response.hits.hits[0]._source


class Organisation(IlsRecord):
    """Organisation class."""

    minter = organisation_id_minter
    fetcher = organisation_id_fetcher
    provider = OrganisationProvider
    model_cls = OrganisationMetadata

    @classmethod
    def get_all(cls):
        """Get all organisations."""
        return sorted([
            Organisation.get_record(_id)
            for _id in Organisation.get_all_ids()
        ], key=lambda org: org.get('name'))

    @classmethod
    def all_code(cls):
        """Get all code."""
        return [org.get('code') for org in cls.get_all()]

    @classmethod
    def get_record_by_viewcode(cls, viewcode):
        """Get record by view code."""
        result = OrganisationsSearch()\
            .filter('term', code=viewcode)\
            .execute()
        if result['hits']['total']['value'] != 1:
            raise Exception(
                'Organisation (get_record_by_viewcode): Result not found.')

        return result['hits']['hits'][0]['_source']

    @classmethod
    def get_record_by_online_harvested_source(cls, source):
        """Get record by online harvested source.

        :param source: the record source
        :return: Organisation record or None.
        """
        results = OrganisationsSearch().filter(
            'term', online_harvested_source=source).scan()
        try:
            return Organisation.get_record_by_pid(next(results).pid)
        except StopIteration:
            return None

    @property
    def organisation_pid(self):
        """Get organisation pid."""
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

    def get_online_locations(self):
        """Get list of online locations."""
        return [
            library.online_location
            for library in self.get_libraries()
            if library.online_location
        ]

    def get_libraries_pids(self):
        """Get all libraries pids related to the organisation."""
        query = LibrariesSearch().source(['pid'])\
            .filter('term', organisation__pid=self.pid)\
            .source('pid')
        return [hit.pid for hit in query.scan()]

    def get_libraries(self):
        """Get all libraries related to the organisation."""
        for pid in self.get_libraries_pids():
            yield Library.get_record_by_pid(pid)

    def get_vendor_pids(self):
        """Get all vendor pids related to the organisation."""
        query = VendorsSearch().source(['pid'])\
            .filter('term', organisation__pid=self.pid)\
            .source('pid')
        return [hit.pid for hit in query.scan()]

    def get_vendors(self):
        """Get all vendors related to the organisation."""
        for pid in self.get_vendor_pids():
            yield Vendor.get_record_by_pid(pid)

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        from rero_ils.modules.acquisition.acq_receipts.api import \
            AcqReceiptsSearch
        library_query = LibrariesSearch()\
            .filter('term', organisation__pid=self.pid)
        receipt_query = AcqReceiptsSearch() \
            .filter('term', organisation__pid=self.pid)
        links = {}
        if get_pids:
            libraries = sorted_pids(library_query)
            receipts = sorted_pids(receipt_query)
        else:
            libraries = library_query.count()
            receipts = receipt_query.count()
        if libraries:
            links['libraries'] = libraries
        if receipts:
            links['acq_receipts'] = receipts
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        return cannot_delete

    def is_test_organisation(self):
        """Check if this is a test organisation."""
        return self.get('code') == 'cypress'


class OrganisationsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Organisation

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='org')
