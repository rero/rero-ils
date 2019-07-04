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

"""API for manipulating item types."""

from __future__ import absolute_import, print_function

from functools import partial

from elasticsearch_dsl import Q
from invenio_search.api import RecordsSearch

from .models import ItemTypeIdentifier
from ..api import IlsRecord
from ..circ_policies.api import CircPoliciesSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

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
        """Check if the name is unique in organisation."""
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

    def get_number_of_items(self):
        """Get number of items."""
        from ..items.api import ItemsSearch
        results = ItemsSearch().filter(
            'term', item_type__pid=self.pid).source().count()
        return results

    def get_number_of_circ_policies(self):
        """Get number of circulation policies."""
        results = CircPoliciesSearch().filter(
            'nested',
            path='settings',
            query=Q(
                'bool',
                must=[
                    Q(
                        'match',
                        settings__item_type__pid=self.pid
                    )
                ]
            )
        ).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        items = self.get_number_of_items()
        if items:
            links['items'] = items
        circ_policies = self.get_number_of_circ_policies()
        if circ_policies:
            links['circ_policies'] = circ_policies
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete
