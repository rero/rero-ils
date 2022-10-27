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

"""Item serializers."""

from csv import QUOTE_ALL, DictWriter

from flask import current_app, request, stream_with_context
from invenio_i18n.ext import current_i18n
from invenio_records_rest.serializers.csv import CSVSerializer, Line

from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin
from rero_ils.utils import get_i18n_supported_languages

from .collector import Collector


class ItemCSVSerializer(CSVSerializer, CachedDataSerializerMixin):
    """Serialize item search for csv."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        # language
        language = request.args.get("lang", current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')

        def generate_csv():
            """Generate CSV records."""

            def _process_item_types_libs_locs(csv_data):
                """Process item types, library and locations data.

                :param csv_data: Dictionary of data.
                """
                itty_pid = csv_data.get('item_type_pid')
                csv_data['item_type'] = self\
                    .get_resource(ItemTypesSearch(), itty_pid)\
                    .get('name')
                # temporary item_type
                if itty_pid := csv_data.pop('temporary_item_type_pid', None):
                    csv_data['temporary_item_type'] = self\
                        .get_resource(ItemTypesSearch(), itty_pid)\
                        .get('name')
                # library
                lib_pid = csv_data.pop('item_library_pid')
                csv_data['item_library_name'] = self\
                    .get_resource(LibrariesSearch(), lib_pid)\
                    .get('name')
                # location
                loc_pid = csv_data.pop('item_location_pid')
                csv_data['item_location_name'] = self\
                    .get_resource(LocationsSearch(), loc_pid)\
                    .get('name')

            headers = dict.fromkeys(self.csv_included_fields)

            # write the CSV output in memory
            line = Line()
            writer = DictWriter(line, quoting=QUOTE_ALL, fieldnames=headers)
            writer.writeheader()
            yield line.read()

            for pids, batch_results in Collector.batch(results=search_result):
                # get documents
                documents = Collector.get_documents_by_item_pids(
                    item_pids=pids, language=language)
                # get loans
                items_stats = Collector.get_loans_by_item_pids(item_pids=pids)
                for hit in batch_results:
                    csv_data = Collector.get_item_data(hit)
                    # _process_item_types_libs_locs(self, csv_data)
                    _process_item_types_libs_locs(csv_data)
                    Collector.append_document_data(csv_data, documents)
                    Collector.append_local_fields(csv_data)
                    # update csv data with loan
                    Collector.append_loan_data(hit, csv_data, items_stats)
                    Collector.append_issue_data(hit, csv_data)
                    # write csv data
                    data = self.process_dict(dictionary=csv_data)
                    writer.writerow(data)
                    yield line.read()

        self.load_all(ItemTypesSearch(), LibrariesSearch(), LocationsSearch())
        return stream_with_context(generate_csv())
