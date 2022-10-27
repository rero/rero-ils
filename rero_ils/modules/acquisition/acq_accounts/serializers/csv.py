# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Acquisition accounts serialization."""

import csv

from flask import stream_with_context
from invenio_records_rest.serializers.csv import CSVSerializer, Line


class AcqAccountCSVSerializer(CSVSerializer):
    """Mixin serializing records as CSV."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        def generate_csv():
            headers = dict.fromkeys(self.csv_included_fields)

            # write the CSV output in memory
            line = Line()
            writer = csv.DictWriter(
                line, quoting=csv.QUOTE_ALL, fieldnames=headers)
            writer.writeheader()
            yield line.read()

            for result in search_result:
                account = result.to_dict()
                csv_data = {
                    'account_pid': account['pid'],
                    'account_name': account.get('name'),
                    'account_number': account.get('number'),
                    'account_allocated_amount':
                        account.get('allocated_amount'),
                    'account_available_amount':
                        account.get('allocated_amount', 0)
                        - account.get('distribution', 0),
                    'account_current_encumbrance':
                        account.get('encumbrance_amount', {}).get('self'),
                    'account_current_expenditure':
                        account.get('expenditure_amount', {}).get('self'),
                    'account_available_balance':
                        account.get('remaining_balance').get('self')
                }
                # write csv data
                data = self.process_dict(csv_data)
                writer.writerow(data)
                yield line.read()

        # return streamed content
        return stream_with_context(generate_csv())
