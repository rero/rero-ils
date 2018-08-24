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

"""API for manipulating members."""

from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from .fetchers import member_id_fetcher
from .minters import member_id_minter
from .providers import MemberProvider


class MembersSearch(RecordsSearch):
    """Members search."""

    class Meta():
        """Meta class."""

        index = 'members'


class Member(IlsRecord):
    """Member class."""

    minter = member_id_minter
    fetcher = member_id_fetcher
    provider = MemberProvider

    @classmethod
    def get_all_member_names(cls):
        """Get all member names."""
        return [n.name for n in MembersSearch().filter(
                "match_all").source(includes=['name']).scan()]

    @classmethod
    def get_all_members(cls):
        """Get all members."""
        return list(MembersSearch().filter("match_all").source().scan())
