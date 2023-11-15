# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

"""Tests REST items Serializer."""

from flask import url_for
from utils import get_csv, login_user

from rero_ils.modules.utils import get_ref_for_pid


def test_serializers(
    client,
    item_lib_martigny,  # on shelf
    document,
    item_lib_fully,  # on loan
    csv_header,
    json_header,
    rero_json_header,
    librarian_martigny,
    loan_due_soon_martigny,
    loc_public_martigny,
    item_type_standard_martigny,
    item_type_on_site_martigny
):
    """Test Serializers."""
    login_user(client, librarian_martigny)

    item = item_lib_martigny
    loc_ref = get_ref_for_pid('locations', loc_public_martigny.pid)
    item.setdefault('temporary_location', {})['$ref'] = loc_ref
    item.commit()
    item.reindex()

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_fully.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert response.json['metadata'].get('item_type', {}).get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_martigny.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert response.json['metadata'].get('item_type', {}).get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item',
        pid_value=item_lib_fully.pid, resolve=1)
    response = client.get(item_url, headers=json_header)
    data = response.json
    assert data['metadata'].get('item_type', {}).get('pid')
    # test if all key exist into response with a value
    for key in ['created', 'updated', 'id', 'links', 'metadata']:
        assert key in data
        assert data[key]

    list_url = url_for('invenio_records_rest.item_list')
    response = client.get(list_url, headers=rero_json_header)
    data = response.json['hits']['hits']
    assert response.status_code == 200

    list_url = url_for('api_item.inventory_search')
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = get_csv(response)
    assert data
    fields = [
        'item_pid', 'item_create_date', 'document_pid', 'document_title',
        'document_creator', 'document_main_type', 'document_sub_type',
        'document_masked', 'document_isbn', 'document_issn',
        'document_series_statement', 'document_edition_statement',
        'document_publication_year', 'document_publisher',
        'document_local_field_1', 'document_local_field_2',
        'document_local_field_3', 'document_local_field_4',
        'document_local_field_5', 'document_local_field_6',
        'document_local_field_7', 'document_local_field_8',
        'document_local_field_9', 'document_local_field_10',
        'item_acquisition_date', 'item_barcode', 'item_call_number',
        'item_second_call_number', 'item_legacy_checkout_count',
        'item_type', 'item_library_name', 'item_location_name',
        'item_pac_code', 'item_holding_pid', 'item_price', 'item_status',
        'item_item_type', 'item_general_note', 'item_staff_note',
        'item_checkin_note', 'item_checkout_note', 'item_acquisition_note',
        'item_binding_note', 'item_condition_note', 'item_patrimonial_note',
        'item_provenance_note', 'temporary_item_type',
        'temporary_item_type_expiry_date', 'item_masked',
        'item_enumerationAndChronology', 'item_local_field_1',
        'item_local_field_2', 'item_local_field_3', 'item_local_field_4',
        'item_local_field_5', 'item_local_field_6', 'item_local_field_7',
        'item_local_field_8', 'item_local_field_9', 'item_local_field_10',
        'issue_status', 'issue_status_date', 'issue_claims_count',
        'issue_expected_date', 'issue_regular', 'item_checkouts_count',
        'item_renewals_count', 'last_transaction_date', 'last_checkout_date'
    ]
    for field in fields:
        assert field in data

    # test provisionActivity without type bf:Publication
    document['provisionActivity'][0]['type'] = 'bf:Manufacture'
    document.commit()
    document.reindex()

    list_url = url_for('api_item.inventory_search')
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = get_csv(response)
    assert data

    # with temporary_item_type
    item_type = item_type_on_site_martigny
    circulation = [
        {'label': 'On site DE', 'language': 'de'},
        {'label': 'On site EN', 'language': 'en'},
        {'label': 'On site FR', 'language': 'fr'},
        {'label': 'On site IT', 'language': 'it'}
    ]
    item_type['circulation_information'] = circulation
    item_type.commit()
    item_type.reindex()
    item['temporary_item_type'] = {
        '$ref': get_ref_for_pid('itty', item_type.pid)
    }
    item.commit()
    item.reindex()
    list_url = url_for('invenio_records_rest.item_list', q=f'pid:{item.pid}')
    response = client.get(list_url, headers=rero_json_header)
    data = response.json['hits']['hits']
    assert circulation == \
        data[0]['metadata']['item_type']['circulation_information']
