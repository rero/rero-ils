# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Patron transactions serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.items.api.api import Item
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

from ..documents.api import DocumentsSearch


class PatronTransactionsJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        records = results.get('hits', {}).get('hits', {})
        for record in records:
            metadata = record.get('metadata', {})
            # Document (if exist)
            document_pid = metadata.get('document', {}).get('pid')
            if document_pid:
                search = DocumentsSearch().filter(
                    'term', pid=document_pid)
                document = list(search.scan())[0].to_dict()
                metadata['document'] = document
            # Loan and item
            loan_pid = metadata.get('loan', {}).get('pid')
            if loan_pid:
                loan = Loan.get_record_by_pid(loan_pid)
                metadata['loan'] = loan
                item_pid = loan.get('item_pid', {}).get('value')
                if item_pid:
                    item = Item.get_record_by_pid(item_pid)
                    metadata['loan']['item'] = item
        return super(PatronTransactionsJSONSerializer, self)\
            .post_process_serialize_search(results, pid_fetcher)


json_patron_transactions = PatronTransactionsJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_patron_transactions_search = search_responsify(
    json_patron_transactions, 'application/rero+json')
