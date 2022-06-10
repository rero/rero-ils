# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""Item serializers."""


import csv

from flask import current_app, request, stream_with_context
from invenio_i18n.ext import current_i18n
from invenio_records_rest.serializers.csv import CSVSerializer, Line

from rero_ils.modules.items.serializers.collector import Collecter
from rero_ils.utils import get_i18n_supported_languages


class ItemCSVSerializer(CSVSerializer):
    """Serialize item search for csv."""

    @classmethod
    def generate_csv(cls, search_result=None, csv_included_fields=None,
                     process_dict=None):
        """Generate CSV records.

        :param search_result: Elasticsearch search result.
        :param csv_included_fields: fields to include.
        :param process_dict: process_dict method.
        """
        headers = dict.fromkeys(csv_included_fields)

        language = request.args.get("lang", current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')

        item_types_map, locations_map, libraries_map = Collecter.mapper()
        # write the CSV output in memory
        line = Line()
        writer = csv.DictWriter(line,
                                quoting=csv.QUOTE_ALL,
                                fieldnames=headers)
        writer.writeheader()
        yield line.read()

        for pids, batch_results in Collecter.batch(results=search_result):
            # get documents
            documents = Collecter.get_documents_by_item_pids(
                item_pids=pids, language=language)
            # get loans
            checkouts, renewals, last_transaction_dates, last_checkouts = \
                Collecter.get_loans_by_item_pids(item_pids=pids)
            for hit in batch_results:
                csv_data = Collecter.get_item_data(hit, item_types_map)
                Collecter.append_library_data(csv_data, libraries_map)
                Collecter.append_location_data(csv_data, locations_map)
                Collecter.append_item_local_fields(csv_data)
                Collecter.append_local_fields(
                    'item', csv_data['item_pid'], csv_data)
                Collecter.append_local_fields(
                    'doc', csv_data['document_pid'], csv_data)
                # update csv data with loan
                csv_data['item_checkouts_count'] = checkouts.get(hit.pid, 0)
                csv_data['item_renewals_count'] = renewals.get(hit.pid, 0)
                csv_data['last_transaction_date'] = last_transaction_dates.get(
                    hit.pid, {}).get('last_transaction_date')
                csv_data['checkout_date'] = last_checkouts.get(
                    hit.pid,  {}).get('checkout_date')
                Collecter.append_issue_data(csv_data)
                # write csv data
                data = process_dict(dictionary=csv_data)
                writer.writerow(data)
                yield line.read()

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        return stream_with_context(
            self.generate_csv(search_result=search_result,
                              csv_included_fields=self.csv_included_fields,
                              process_dict=self.process_dict))
