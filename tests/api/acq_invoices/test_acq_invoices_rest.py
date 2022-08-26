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

"""Tests REST API acquisition invoices."""

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acquisition_invoices_library_facets(
        client, org_martigny, acq_invoice_fiction_martigny, rero_json_header):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.acin_list', view='org1')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']
    assert 'library' in aggs


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acquisition_invoice_total_amount(
        client, acq_invoice_fiction_martigny):
    """Test calculate total amonut of invoice."""
    item_url = url_for('invenio_records_rest.acin_item', pid_value='acin1')
    acq_invoice = acq_invoice_fiction_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['invoice_price'] == 1500


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acquisition_invoice_get(client, acq_invoice_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acin_item', pid_value='acin1')
    acq_invoice = acq_invoice_fiction_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{acq_invoice.revision_id}"'

    data = get_json(res)
    assert acq_invoice.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert acq_invoice.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.acin_list', pid='acin1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == acq_invoice.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acquisition_invoices_post_put_delete(
        client, org_martigny, vendor2_martigny, acq_invoice_fiction_saxon,
        json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.acin_item', pid_value='1')
    list_url = url_for('invenio_records_rest.acin_list', q='pid:1')

    acq_invoice_fiction_saxon['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.acin_list',
        acq_invoice_fiction_saxon
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == acq_invoice_fiction_saxon

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert acq_invoice_fiction_saxon == data['metadata']

    # Update record/PUT
    data = acq_invoice_fiction_saxon
    data['invoice_number'] = 'IN-TEST-2'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['invoice_number'] == 'IN-TEST-2'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['invoice_number'] == 'IN-TEST-2'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['invoice_number'] == 'IN-TEST-2'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_acquisition_invoices_can_delete(client, acq_invoice_fiction_martigny):
    """Test can delete an acquisition invoice."""
    can, reasons = acq_invoice_fiction_martigny.can_delete
    assert can
    assert reasons == {}


def test_filtered_acquisition_invoices_get(
        client, librarian_martigny, acq_invoice_fiction_martigny,
        acq_invoice_fiction_saxon, librarian_sion,
        acq_invoice_fiction_sion):
    """Test acquisition invoices filter by organisation."""
    list_url = url_for('invenio_records_rest.acin_list')

    res = client.get(list_url)
    assert res.status_code == 401

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.acin_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.acin_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_acquisition_invoice_properties(
        org_sion, vendor_sion, document, lib_sion, acq_invoice_fiction_sion):
    """Test acquisition invoice properties."""
    assert acq_invoice_fiction_sion.vendor_pid == vendor_sion.pid
    assert acq_invoice_fiction_sion.library_pid == lib_sion.pid
    assert acq_invoice_fiction_sion.organisation_pid == org_sion.pid
