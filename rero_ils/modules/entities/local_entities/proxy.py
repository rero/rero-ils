# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Local entity proxies."""
from elasticsearch_dsl import Q

from .api import LocalEntitiesSearch
from ..models import EntityType

CATEGORY_FILTERS = {
    'agents': Q('terms', type=[EntityType.PERSON, EntityType.ORGANISATION]),
    'person': Q('term', type=EntityType.PERSON),
    'organisation': Q('term', type=EntityType.ORGANISATION),
    'concepts': Q('term', type=EntityType.TOPIC),
    'concepts-genreForm':
        Q('term', type=EntityType.TOPIC) & Q('term', genreForm=True)
}


class LocalEntityProxy:
    """Local entity proxy."""

    def __init__(self, category):
        """Init magic method.

        :param category: the search category ('agents', 'organisation', ...).
        """
        self.category = category

    def search(self, search_term, size=10):
        """Search for local entities.

        :param search_term: the search term.
        :param size: the number of hit to return.
        :return: local entities matching the search term.
        :rtype: generator.
        """
        query = self._create_base_query()[:size]\
            .filter('query_string', query=search_term)
        yield from query.execute()

    def _create_base_query(self):
        """Build the base ES query object to search `LocalEntity`.

        Either the search_category is key for a predefined configuration,
        either the search_category will be used as local entity type search
        term.
        """
        query = LocalEntitiesSearch()
        if self.category in CATEGORY_FILTERS:
            return query.filter(CATEGORY_FILTERS[self.category])
        else:
            return query.filter('term', type=self.category)
