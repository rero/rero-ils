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

"""RERO Entity JSON serialization."""

from rero_ils.modules.serializers import JSONSerializer


class EntityJSONSerializer(JSONSerializer):
    """Serializer for RERO-ILS `Document` records as JSON."""

    def _postprocess_search_links(self, search_results, pid_fetcher) -> None:
        """Post-process search links.

        :param search_results: Elasticsearch search result.
        :param pid_fetcher: Persistent identifier fetcher related to records
                            into the search result.
        """
        # DEV NOTES :
        # We need to override this method to remove the `create` link from
        # search results.
        # See `rero_ils.modules.serializers.mixins.PostprocessorMixin`
