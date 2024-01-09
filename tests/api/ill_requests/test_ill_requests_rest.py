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

"""Tests REST API item types."""

import json
from copy import deepcopy
from datetime import datetime

import mock
from dateutil.relativedelta import *
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.ill_requests.api import ILLRequest
from rero_ils.modules.ill_requests.models import ILLRequestStatus


def test_ill_requests_permissions(client, ill_request_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.illr_item', pid_value='illr1')

    # Anonymous user
    res = client.get(item_url)
    assert res.status_code == 401
    res, _ = postdata(client, 'invenio_records_rest.illr_list', {})
    assert res.status_code == 401
    res = client.put(item_url, data={}, headers=json_header)
    assert res.status_code == 401
    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_ill_requests_facets(client, ill_request_martigny, rero_json_header):
    """Test record retrieval."""
    url = url_for('invenio_records_rest.illr_list', view='org1')
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    facets = ['library']
    assert all(facet_name in data['aggregations'] for facet_name in facets)
    aggr_library = data['aggregations']['library']
    assert all('name' in term for term in aggr_library['buckets'])


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_ill_requests_get(client, ill_request_martigny):
    """Test record retrieval."""
    ill_request = ill_request_martigny
    item_url = url_for('invenio_records_rest.illr_item', pid_value='illr1')
    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{ill_request.revision_id}"'

    data = get_json(res)
    assert ill_request.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert ill_request.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.illr_list', pid='illr1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    metadata = data['hits']['hits'][0]['metadata']
    del metadata['organisation']  # organisation is added only for indexation
    del metadata['library']  # library is added only for indexation
    del metadata['patron']['name']  # patron name is added only for indexation
    assert metadata == ill_request.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_ill_requests_post_put_delete(client, org_martigny, json_header,
                                      patron_martigny,
                                      loc_public_martigny,
                                      ill_request_martigny_data):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.illr_item', pid_value='1')
    list_url = url_for('invenio_records_rest.illr_list', q='pid:1')

    ill_request_data = deepcopy(ill_request_martigny_data)
    ill_request_data['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.illr_list',
        ill_request_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == ill_request_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert ill_request_data == data['metadata']

    # Update record/PUT
    data = ill_request_data
    data['document']['title'] = 'Title test'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['document']['title'] == 'Title test'
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['metadata']['document']['title'] == 'Title test'
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['document']['title'] == 'Title test'


def test_ill_requests_can_delete(client, ill_request_martigny):
    """Test can delete an ill request."""
    can, reasons = ill_request_martigny.can_delete
    assert can
    assert reasons == {}


def test_filtered_ill_requests_get(
        client, librarian_martigny, ill_request_martigny,
        librarian_sion, ill_request_sion):
    """Test ill_requests filter by organisation."""
    list_url = url_for('invenio_records_rest.illr_list')
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    pids = [hit['metadata']['pid'] for hit in data['hits']['hits']]
    assert ill_request_martigny.pid in pids

    # Sion
    login_user_via_session(client, librarian_sion.user)
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    pids = [hit['metadata']['pid'] for hit in data['hits']['hits']]
    assert ill_request_sion.pid in pids


def test_ill_request_secure_api(client, json_header, ill_request_martigny,
                                ill_request_martigny_data, ill_request_sion,
                                librarian_martigny,
                                system_librarian_sion):
    """Test ill request secure api access."""
    martigny_url = url_for('invenio_records_rest.illr_item',
                           pid_value=ill_request_martigny.pid)
    sion_url = url_for('invenio_records_rest.illr_item',
                       pid_value=ill_request_sion.pid)
    # Logged as Martigny librarian
    #   * can read martigny request
    #   * can't read sion request
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(martigny_url)
    assert res.status_code == 200
    res = client.get(sion_url)
    assert res.status_code == 403


def test_ill_request_secure_api_update(client, json_header,
                                       ill_request_martigny_data,
                                       ill_request_martigny, ill_request_sion,
                                       system_librarian_martigny,
                                       system_librarian_sion):
    """Test ill request secure api update."""
    martigny_url = url_for('invenio_records_rest.illr_item',
                           pid_value=ill_request_martigny.pid)
    sion_url = url_for('invenio_records_rest.illr_item',
                       pid_value=ill_request_sion.pid)
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    data = ill_request_martigny_data
    data['document']['title'] = 'Test title'
    res = client.put(
        martigny_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, system_librarian_sion.user)
    res = client.put(
        martigny_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_ill_request_secure_api_delete(client, ill_request_martigny,
                                       ill_request_sion,
                                       system_librarian_martigny):
    """Test ill requests secure api delete."""
    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for(
        'invenio_records_rest.illr_item',
        pid_value=ill_request_sion.pid
    )
    res = client.delete(record_url)
    assert res.status_code == 403
    record_url = url_for(
        'invenio_records_rest.illr_item',
        pid_value=ill_request_martigny.pid
    )
    res = client.delete(record_url)
    assert res.status_code == 403


def test_filtered_ill_requests_get_pending_months_filters(
        client, app, db, librarian_martigny, ill_request_martigny):
    """Test ill_requests filter by pending and months."""

    def date_delta(months):
        """Date delta."""
        return datetime.now() - relativedelta(months=months)

    def db_commit_reindex(record):
        """DB commit and reindex."""
        db.session.merge(record.model)
        db.session.commit()
        record.reindex()

    login_user_via_session(client, librarian_martigny.user)

    # Initial status is pending
    list_url = url_for(
        'invenio_records_rest.illr_list',
        q='pid:'+ill_request_martigny['pid']
    )
    res = client.get(list_url)
    result = res.json
    assert result['hits']['total']['value'] == 1

    # Change created date
    initial_create = ill_request_martigny.model.created
    ill_request_martigny.model.created = date_delta(7)
    db_commit_reindex(ill_request_martigny)

    list_url = url_for(
        'invenio_records_rest.illr_list',
        q='pid:'+ill_request_martigny['pid']
    )
    res = client.get(list_url)
    result = res.json
    assert result['hits']['total']['value'] == 1

    # closed 7 months
    ill_request_martigny = ILLRequest\
        .get_record_by_pid(ill_request_martigny.pid)
    ill_request_martigny['status'] = ILLRequestStatus.CLOSED
    ill_request_martigny.update(
        ill_request_martigny, dbcommit=True, reindex=True)

    list_url = url_for(
        'invenio_records_rest.illr_list',
        q='pid:'+ill_request_martigny['pid']
    )
    res = client.get(list_url)
    result = res.json
    assert result['hits']['total']['value'] == 0

    # Change delta
    app.config['RERO_ILS_ILL_HIDE_MONTHS'] = 8

    list_url = url_for(
        'invenio_records_rest.illr_list',
        q='pid:'+ill_request_martigny['pid']
    )
    res = client.get(list_url)
    result = res.json
    assert result['hits']['total']['value'] == 1

    # Initial state
    ill_request_martigny.model.created = initial_create
    db_commit_reindex(ill_request_martigny)
    ill_request_martigny = ILLRequest\
        .get_record_by_pid(ill_request_martigny.pid)
    ill_request_martigny['status'] = ILLRequestStatus.PENDING
    ill_request_martigny.update(
        ill_request_martigny, dbcommit=True, reindex=True)
