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

"""Items serializers."""
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from rero_ils.modules.items.serializers.response import search_responsify_csv
from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

from .csv import ItemCSVSerializer
from .json import ItemsJSONSerializer

csv_included_fields = [
        'item_pid',
        'item_create_date',
        'document_pid',
        'document_title',
        'document_creator',
        'document_main_type',
        'document_sub_type',
        'document_masked',
        'document_isbn',
        'document_issn',
        'document_series_statement',
        'document_edition_statement',
        'document_publication_year',
        'document_publisher',
        'document_local_field_1',
        'document_local_field_2',
        'document_local_field_3',
        'document_local_field_4',
        'document_local_field_5',
        'document_local_field_6',
        'document_local_field_7',
        'document_local_field_8',
        'document_local_field_9',
        'document_local_field_10',
        'item_acquisition_date',
        'item_barcode',
        'item_call_number',
        'item_second_call_number',
        'item_legacy_checkout_count',
        'item_type',
        'item_library_name',
        'item_location_name',
        'item_pac_code',
        'item_holding_pid',
        'item_price',
        'item_status',
        'item_item_type',
        'item_general_note',
        'item_staff_note',
        'item_checkin_note',
        'item_checkout_note',
        'item_acquisition_note',
        'item_binding_note',
        'item_condition_note',
        'item_patrimonial_note',
        'item_provenance_note',
        'temporary_item_type',
        'temporary_item_type_expiry_date',
        'item_masked',
        'item_enumerationAndChronology',
        'item_local_field_1',
        'item_local_field_2',
        'item_local_field_3',
        'item_local_field_4',
        'item_local_field_5',
        'item_local_field_6',
        'item_local_field_7',
        'item_local_field_8',
        'item_local_field_9',
        'item_local_field_10',
        'issue_status',
        'issue_status_date',
        'issue_claims_count',
        'issue_expected_date',
        'issue_regular',
        'item_checkouts_count',
        'item_renewals_count',
        'last_transaction_date',
        'checkout_date'
]

csv_item = ItemCSVSerializer(
    JSONSerializer,
    csv_included_fields=csv_included_fields
)
csv_item_response = record_responsify(csv_item, "text/csv")
csv_item_search = search_responsify_csv(csv_item, "text/csv")
"""CSV serializer."""

json_item = ItemsJSONSerializer(RecordSchemaJSONV1)
"""JSON serializer."""

json_item_search = search_responsify(json_item, 'application/rero+json')
json_item_response = record_responsify(json_item, 'application/rero+json')
