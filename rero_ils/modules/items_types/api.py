# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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

"""API for manipulating items_types."""

from __future__ import absolute_import, print_function

from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from .fetchers import item_type_id_fetcher
from .minters import item_type_id_minter
from .providers import ItemTypeProvider


class ItemTypeSearch(RecordsSearch):
    """PatronTypeSearch."""

    class Meta:
        """Search only on patrons index."""

        index = 'items_types'


class ItemType(IlsRecord):
    """ItemType class."""

    minter = item_type_id_minter
    fetcher = item_type_id_fetcher
    provider = ItemTypeProvider

    @property
    def can_delete(self):
        """Record can be deleted."""
        return True

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique on organisation."""
        patron_type = ItemTypeSearch().filter(
            'term',
            **{"name": name}
        ).filter(
            'term',
            **{"organisation_pid": organisation_pid}
        ).source().scan()
        result = list(patron_type)
        if len(result) > 0:
            return result.pop(0)
        else:
            return None
