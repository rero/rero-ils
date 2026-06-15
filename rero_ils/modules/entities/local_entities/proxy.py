# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity proxies."""

from elasticsearch_dsl import Q

from ..models import EntityType
from .api import LocalEntitiesSearch

CATEGORY_FILTERS = {
    "agents": Q("terms", type=[EntityType.PERSON, EntityType.ORGANISATION]),
    "person": Q("term", type=EntityType.PERSON),
    "organisation": Q("term", type=EntityType.ORGANISATION),
    "concepts": Q("term", type=EntityType.TOPIC),
    "concepts_genreForm": Q("term", type=EntityType.TOPIC) & Q("term", genreForm=True),
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
        query = self._create_base_query()[:size].filter("query_string", query=search_term)
        yield from query.execute()

    def _create_base_query(self):
        """Build the base search query object to search `LocalEntity`.

        Either the search_category is key for a predefined configuration,
        either the search_category will be used as local entity type search
        term.
        """
        query = LocalEntitiesSearch()
        if self.category in CATEGORY_FILTERS:
            return query.filter(CATEGORY_FILTERS[self.category])
        return query.filter("term", type=self.category)
