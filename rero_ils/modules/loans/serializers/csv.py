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

"""RERO-ILS Loan resource serializers for CSV format."""

from csv import QUOTE_ALL, DictWriter

import ciso8601
from flask import stream_with_context
from invenio_records_rest.serializers.csv import CSVSerializer, Line

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.extensions import TitleExtension
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    StreamSerializerMixin

from ..utils import get_loan_checkout_date


class LoanStreamedCSVSerializer(CSVSerializer, StreamSerializerMixin,
                                CachedDataSerializerMixin):
    """Streamed CSV serializer for `loan` resource."""

    def transform_search_hit(self, hit_pid, hit, links_factory=None,
                             **kwargs):
        """Transform search result hit into a desired representation.

        :param hit_pid: Pid of the resource.
        :param hit: Record metadata retrieved via search.
        :param links_factory: Factory function for record links.
        """
        date_format = '%Y-%m-%d'
        # Transform ISO dates to human-readable strings
        for field in ['end_date', 'request_expire_date']:
            if field in hit:
                hit[field] = ciso8601.parse_datetime(hit[field])\
                    .strftime(date_format)
        if checkout_date := get_loan_checkout_date(hit_pid):
            hit['checkout_date'] = checkout_date.strftime(date_format)

        # Convert PID references to human-readable name
        lib_loader_ref = LibrariesSearch()
        pid_reference_fields = [
            (lib_loader_ref, 'owning_library', 'library_pid'),
            (lib_loader_ref, 'pickup_library', 'pickup_library_pid'),
            (lib_loader_ref, 'transaction_library', 'transaction_library_pid'),
            (PatronTypesSearch(), 'patron_type', 'patron_type_pid')
        ]
        for loader, field, pid_reference in pid_reference_fields:
            if pid := hit.pop(pid_reference, None):
                hit[field] = self.get_resource(loader, pid).get('name')

        # document information dumping
        if doc := self.get_resource(DocumentsSearch(), hit['document_pid']):
            hit['document_title'] = \
                TitleExtension.format_text(doc.get('title'))

        # Item information dumping
        if item := self.get_resource(ItemsSearch(), hit['item_pid']['value']):
            hit['item_call_numbers'] = '|'.join(filter(None, [
                item.get('call_number'), item.get('second_call_number')
            ]))
            hit['item_barcode'] = item.get('barcode')

        # Patron information's dumping
        if patron := self.get_resource(Patron, hit['patron_pid']):
            hit['patron_name'] = patron.formatted_name
            hit['patron_email'] = patron.user.email
            hit['patron_barcode'] = '|'.join(
                patron.get('patron', {}).get('barcode', [])
            )
        return hit

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """

        def generate_csv():
            """Generate the CSV content as a generator.

            :returns: a generator of line to output into the csv file.
            """
            headers = dict.fromkeys(self.csv_included_fields)

            # write the CSV output in memory
            line = Line()
            writer = DictWriter(line, quoting=QUOTE_ALL, fieldnames=headers)
            writer.writeheader()
            yield line.read()

            for pids, records in self.get_chunks(search_result):
                # load in cache (with one single call) all items and documents
                # from this chunks
                item_pids, document_pids = [], []
                for record in records:
                    document_pids.append(record['document_pid'])
                    item_pids.append(record['item_pid']['value'])
                self.load_resources(DocumentsSearch(), document_pids)
                self.load_resources(ItemsSearch(), item_pids)

                for record in records:
                    row_data = self.process_dict(self.transform_search_hit(
                        record.pid,
                        record.to_dict()
                    ))
                    writer.writerow(row_data)
                    yield line.read()

        self.load_all(LibrariesSearch(), PatronTypesSearch())
        return stream_with_context(generate_csv())
