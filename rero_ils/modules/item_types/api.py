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

"""API for manipulating item_types."""

from __future__ import absolute_import, print_function

from functools import partial

from invenio_search.api import RecordsSearch

from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from .models import ItemTypeIdentifier

# provider
ItemTypeProvider = type(
    'ItemTypeProvider',
    (Provider,),
    dict(identifier=ItemTypeIdentifier, pid_type='itty')
)
# minter
item_type_id_minter = partial(id_minter, provider=ItemTypeProvider)
# fetcher
item_type_id_fetcher = partial(id_fetcher, provider=ItemTypeProvider)


class ItemTypesSearch(RecordsSearch):
    """ItemTypeSearch."""

    class Meta:
        """Search only on item_types index."""

        index = 'item_types'


class ItemType(IlsRecord):
    """ItemType class."""

    minter = item_type_id_minter
    fetcher = item_type_id_fetcher
    provider = ItemTypeProvider

    # @property
    # def can_delete(self):
    #     """Record can be deleted."""
    #     from ..documents_items.api import DocumentsSearch

    #     search = (
    #         DocumentsSearch()
    #         .filter('term', **{'itemslist.item_type_pid': self.pid})
    #         .source()
    #         .scan()
    #     )
    #     return search.count() == 0

    @classmethod
    def get_pid_by_name(cls, name):
        """Get pid by name."""
        pid = None
        try:
            pids = [
                n.pid
                for n in ItemTypesSearch()
                .filter('term', item_type_name=name)
                .source(includes=['pid'])
                .scan()
            ]
            if len(pids) > 0:
                pid = pids[0]
        except Exception:
            pass
            # needs app_context to work, but is called before
        return pid

    @classmethod
    def exist_name_and_organisation_pid(cls, name, organisation_pid):
        """Check if the name is unique on organisation."""
        item_type = (
            ItemTypesSearch()
            .filter('term', item_type_name=name)
            .filter('term', organisation__pid=organisation_pid)
            .source()
            .scan()
        )
        result = list(item_type)
        if len(result) > 0:
            return result.pop(0)
        else:
            return None
