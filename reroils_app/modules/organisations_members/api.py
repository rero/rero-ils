# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating members associated to a organisation."""

from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata

from ..api import RecordWithElements
from ..members_locations.api import MemberWithLocations
from ..organisations.api import Organisation
from ..organisations.fetchers import organisation_id_fetcher
from ..organisations.minters import organisation_id_minter
from ..organisations.providers import OrganisationProvider
from .models import OrganisationsMembersMetadata


class OrganisationWithMembers(RecordWithElements):
    """Api for Documents with Items."""

    record = Organisation
    element = MemberWithLocations
    metadata = OrganisationsMembersMetadata
    elements_list_name = 'members'
    minter = organisation_id_minter
    fetcher = organisation_id_fetcher
    provider = OrganisationProvider

    # @property
    # def elements(self):
    #     """Return an array of Members."""
    #     if self.model is None:
    #         raise MissingModelError()
    #
    #     # retrive all members in the relation table
    #     # sorted by members creation date
    #     organisations_members = self.metadata.query\
    #         .filter_by(organisation_id=self.id)\
    #         .join(self.metadata.member)\
    #         .order_by(RecordMetadata.created)
    #     to_return = []
    #     for org_memb in organisations_members:
    #         member = MemberWithLocations.get_record_by_id(org_memb.member.id)
    #         to_return.append(member)
    #     return to_return

    @property
    def members(self):
        """Members."""
        return self.elements

    def add_member(self, member, dbcommit=False, reindex=False):
        """Add an member."""
        super(OrganisationWithMembers, self).add_element(
            member,
            dbcommit=dbcommit,
            reindex=reindex
        )

    def remove_member(self, member, force=False, delindex=False):
        """Remove an member."""
        super(OrganisationWithMembers, self).remove_element(
            member,
            force=force,
            delindex=delindex
        )

    @classmethod
    def get_organisation_by_memberid(cls, id_, with_deleted=False):
        """Retrieve the organisation by member id."""
        return super(OrganisationWithMembers, cls).get_record_by_elementid(
            id_, with_deleted
        )
