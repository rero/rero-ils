# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Acquisition order serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.acq_orders.serializers.csv import AcqOrderCSVSerializer
from rero_ils.modules.acq_orders.serializers.json import AcqOrderJSONSerializer
from rero_ils.modules.items.serializers import search_responsify_csv
from rero_ils.modules.response import search_responsify_file
from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

json_acq_order = AcqOrderJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_acor_search = search_responsify(json_acq_order, 'application/rero+json')

"""CSV serializer."""
csv_acor = AcqOrderCSVSerializer(
    csv_included_fields=[
        'order_pid', 'order_reference', 'order_date', 'order_staff_note',
        'order_vendor_note', 'order_type', 'order_status', 'vendor_name',
        'document_pid', 'document_creator', 'document_title',
        'document_publisher', 'document_publication_year',
        'document_edition_statement', 'document_series_statement',
        'document_isbn', 'account_name', 'account_number',
        'order_lines_priority', 'order_lines_notes', 'order_lines_status',
        'ordered_quantity', 'ordered_unit_price', 'ordered_amount',
        'receipt_reference', 'received_quantity', 'received_amount',
        'receipt_date'
    ]
)

csv_acor_search = search_responsify_file(csv_acor, 'text/csv',  'csv')
"""CSV search serializer."""
