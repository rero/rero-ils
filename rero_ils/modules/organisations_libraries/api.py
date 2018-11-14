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

"""API for manipulating libraries associated to a organisation."""

from ..api import RecordWithElements
from ..libraries_locations.api import LibraryWithLocations
from ..organisations.api import Organisation
from ..organisations.fetchers import organisation_id_fetcher
from ..organisations.minters import organisation_id_minter
from ..organisations.providers import OrganisationProvider
from .models import OrganisationsLibrariesMetadata


class OrganisationWithLibraries(RecordWithElements):
    """Api for Documents with Items."""

    record = Organisation
    element = LibraryWithLocations
    metadata = OrganisationsLibrariesMetadata
    elements_list_name = 'libraries'
    minter = organisation_id_minter
    fetcher = organisation_id_fetcher
    provider = OrganisationProvider

    # @property
    # def elements(self):
    #     """Return an array of Libraries."""
    #     if self.model is None:
    #         raise MissingModelError()
    #
    #     # retrive all libraries in the relation table
    #     # sorted by libraries creation date
    #     organisations_libraries = self.metadata.query\
    #         .filter_by(organisation_id=self.id)\
    #         .join(self.metadata.library)\
    #         .order_by(RecordMetadata.created)
    #     to_return = []
    #     for org_lib in organisations_libraries:
    #         library =\
    #             LibraryWithLocations.get_record_by_id(org_lib.library.id)
    #         to_return.append(library)
    #     return to_return

    @property
    def libraries(self):
        """Libraries."""
        return self.elements

    def add_library(self, library, dbcommit=False, reindex=False):
        """Add an library."""
        super(OrganisationWithLibraries, self).add_element(
            library, dbcommit=dbcommit, reindex=reindex
        )

    def remove_library(self, library, force=False, delindex=False):
        """Remove an library."""
        super(OrganisationWithLibraries, self).remove_element(
            library, force=force, delindex=delindex
        )

    @classmethod
    def get_organisation_by_libraryid(cls, id_, with_deleted=False):
        """Retrieve the organisation by library id."""
        return super(OrganisationWithLibraries, cls).get_record_by_elementid(
            id_, with_deleted
        )
