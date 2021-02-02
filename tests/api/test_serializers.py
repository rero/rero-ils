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

"""Tests Serializers."""


from flask import url_for
from utils import get_csv, get_json, login_user


def test_patrons_serializers(
    client,
    json_header,
    librarian_martigny,
    librarian2_martigny
):
    """Test serializers for patrons."""
    login_user(client, librarian_martigny)

    list_url = url_for('invenio_records_rest.ptrn_list')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200

    # Get the first result and check if it contains all desired keys.
    data = get_json(response)
    hit = data['hits']['hits'][0]
    for key in ['created', 'updated', 'id', 'links', 'metadata']:
        assert key in hit
        assert hit[key]


def test_items_serializers(
    client,
    item_lib_martigny,  # on shelf
    item_lib_fully,  # on loan
    csv_header,
    json_header,
    rero_json_header,
    patron_martigny,
    librarian_martigny,
    librarian_sion,
    loan_pending_martigny
):
    """Test record retrieval."""
    login_user(client, librarian_martigny)

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_fully.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    assert data['metadata'].get('item_type', {}).get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_martigny.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    assert data['metadata'].get('item_type', {}).get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item',
        pid_value=item_lib_fully.pid, resolve=1)
    response = client.get(item_url, headers=json_header)
    data = get_json(response)
    assert data['metadata'].get('item_type', {}).get('pid')
    # test if all key exist into response with a value
    for key in ['created', 'updated', 'id', 'links', 'metadata']:
        assert key in data
        assert data[key]

    list_url = url_for('invenio_records_rest.item_list')
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200

    list_url = url_for('invenio_records_rest.item_list')
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = get_csv(response)
    assert data
    assert '"pid","document_pid","document_title","document_creator",' \
           '"document_main_type","document_sub_type","location_name",' \
           '"barcode","call_number","second_call_number",' \
           '"enumerationAndChronology","loans_count",' \
           '"last_transaction_date","status","created"' in data
