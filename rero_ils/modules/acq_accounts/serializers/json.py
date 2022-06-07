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

"""Acquisition account serialization."""

from rero_ils.modules.libraries.api import Library
from rero_ils.modules.serializers import JSONSerializer

from ..api import AcqAccountsSearch


class AcqAccountJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        # Add some ES stored keys into response
        try:
            es_hit = next(AcqAccountsSearch()
                          .filter('term', pid=record.pid)
                          .source().scan()).to_dict()
            keys = ['depth', 'distribution', 'is_active',
                    'encumbrance_exceedance', 'expenditure_exceedance',
                    'encumbrance_amount', 'expenditure_amount',
                    'remaining_balance']
            for key in keys:
                value = es_hit.get(key)
                if value is not None:
                    record[key] = value
        except StopIteration:
            # Should not happens... the account should always be indexed
            pass

        return super().preprocess_record(
            pid=pid,
            record=record,
            links_factory=links_factory,
            kwargs=kwargs
        )

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        # Add library name
        for lib_term in results.get('aggregations', {}).get(
                'library', {}).get('buckets', []):
            pid = lib_term.get('key')
            lib_term['name'] = Library.get_record_by_pid(pid).get('name')
        return super().post_process_serialize_search(results, pid_fetcher)
