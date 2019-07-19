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

"""API for manipulating organisation."""


from functools import partial

from invenio_search.api import RecordsSearch

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


class OrganisationSearch(RecordsSearch):
    """Organisation search."""

    class Meta():
        """Meta class."""

        index = 'organisations'


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
        result = OrganisationSearch().filter(
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
