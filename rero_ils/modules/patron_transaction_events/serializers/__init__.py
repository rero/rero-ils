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

"""Patron transaction event serializers."""

from rero_ils.modules.serializers import RecordSchemaJSONV1, \
    search_responsify, search_responsify_file

from .csv import PatronTransactionEventCSVSerializer
from .json import PatronTransactionEventsJSONSerializer

__all__ = [
    'json_ptre_search',
    'csv_ptre_search'
]


"""JSON serializer."""
_json = PatronTransactionEventsJSONSerializer(RecordSchemaJSONV1)
json_ptre_search = search_responsify(_json, 'application/rero+json')

"""CSV serializer."""
_csv = PatronTransactionEventCSVSerializer(
    csv_included_fields=[
        'category',
        'type',
        'subtype',
        'transaction_date',
        'amount',
        'patron_name',
        'patron_barcode',
        'patron_email',
        'patron_type',
        'document_pid',
        'document_title',
        'item_barcode',
        'item_owning_library',
        'transaction_library',
        'operator_name'
    ]
)

csv_ptre_search = search_responsify_file(
    _csv,
    'text/csv',
    file_extension='csv',
    file_prefix='export-fees'
)
