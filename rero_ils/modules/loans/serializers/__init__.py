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

"""RERO-ILS Loan resource serializers."""
from rero_ils.modules.serializers import RecordSchemaJSONV1, \
    search_responsify, search_responsify_file

from .csv import LoanStreamedCSVSerializer
from .json import LoanJSONSerializer

__all__ = [
    'json_loan_search',
    'csv_stream_search'
]


_json = LoanJSONSerializer(RecordSchemaJSONV1)
_streamed_csv = LoanStreamedCSVSerializer(
    csv_included_fields=[
        'pid',
        'document_title',
        'item_barcode',
        'item_call_numbers',
        'patron_name',
        'patron_barcode',
        'patron_email',
        'patron_type',
        'owning_library',
        'transaction_library',
        'pickup_library',
        'state',
        'checkout_date',
        'end_date',
        'request_expire_date',
    ]
)

json_loan_search = search_responsify(_json, 'application/rero+json')
csv_stream_search = search_responsify_file(
    _streamed_csv,
    'text/csv',
    file_extension='csv',
    file_prefix='export-loans'
)
