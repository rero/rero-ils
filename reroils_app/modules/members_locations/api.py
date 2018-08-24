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

"""API for manipulating locations associated to a members."""


from ..api import RecordWithElements
from ..locations.api import Location
from ..members.api import Member
from ..members.fetchers import member_id_fetcher
from ..members.minters import member_id_minter
from ..members.providers import MemberProvider
from .models import MembersLocationsMetadata


class MemberWithLocations(RecordWithElements):
    """Api for Documents with Items."""

    record = Member
    element = Location
    metadata = MembersLocationsMetadata
    elements_list_name = 'locations'
    minter = member_id_minter
    fetcher = member_id_fetcher
    provider = MemberProvider

    # @property
    # def elements(self):
    #     """Return an array of Locations."""
    #     if self.model is None:
    #         raise MissingModelError()
    #
    #     # retrive all members in the relation table
    #     # sorted by members creation date
    #     members_locations = self.metadata.query\
    #         .filter_by(member_id=self.id)\
    #         .join(self.metadata.location)\
    #         .order_by(RecordMetadata.created)
    #     to_return = []
    #     for memb_loc in members_locations:
    #         location = Location.get_record_by_id(memb_loc.location.id)
    #         to_return.append(location)
    #     return to_return

    @property
    def locations(self):
        """Locations."""
        return self.elements

    def add_location(self, location, dbcommit=False, reindex=False):
        """Add an location."""
        super(MemberWithLocations, self).add_element(
            location,
            dbcommit=dbcommit,
            reindex=reindex
        )

    def remove_location(self, location, force=False, delindex=False):
        """Remove an location."""
        super(MemberWithLocations, self).remove_element(
            location,
            force=force,
            delindex=delindex
        )

    @classmethod
    def get_member_by_locationid(cls, id_, with_deleted=False):
        """Retrieve the member by location id."""
        return super(MemberWithLocations, cls).get_record_by_elementid(
            id_, with_deleted
        )

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(MemberWithLocations, self).dumps(*kwargs)
        for item in data.get('itemslist', []):
            pid, location = Location.get_location(item.get('location_pid'))
            if location:
                item['location_name'] = location.get('name')
                member = Member.get_member_by_locationid(location.id)
                if member:
                    item['member_pid'] = member.pid
        return data
