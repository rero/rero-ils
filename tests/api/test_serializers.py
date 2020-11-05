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
    librarian_martigny_no_email,
    librarian2_martigny_no_email
):
    """Test serializers for patrons."""
    login_user(client, librarian_martigny_no_email)

    list_url = url_for('invenio_records_rest.ptrn_list')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200


def test_items_serializers(
    client,
    item_lib_martigny,  # on shelf
    item_lib_fully,  # on loan
    csv_header,
    json_header,
    rero_json_header,
    patron_martigny_no_email,
    librarian_martigny_no_email,
    librarian_sion_no_email,
    loan_pending_martigny
):
    """Test record retrieval."""
    login_user(client, librarian_martigny_no_email)

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_fully.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    assert data['metadata'].get('item_type').get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_martigny.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    assert data['metadata'].get('item_type').get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item',
        pid_value=item_lib_fully.pid, resolve=1)
    response = client.get(item_url, headers=json_header)
    data = get_json(response)['metadata']
    assert data.get('item_type').get('pid')

    list_url = url_for('invenio_records_rest.item_list')
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200

    list_url = url_for('invenio_records_rest.item_list')
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = get_csv(response)
    assert data
    assert '"pid","document_pid","document_title","document_creator",' \
           '"document_type","location_name","barcode","call_number",' \
           '"second_call_number","enumerationAndChronology",' \
           '"loans_count","last_transaction_date","status","created"' in data
