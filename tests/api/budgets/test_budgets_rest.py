# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Tests REST API acquisition accounts."""

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url


def test_budgets_permissions(client, budget_2020_martigny,
                             json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.budg_item', pid_value='budg1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.budg_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.budg_item', pid_value='budg1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_budgets_get(client, budget_2020_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.budg_item', pid_value='budg1')
    budget = budget_2020_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{budget.revision_id}"'

    data = get_json(res)
    assert budget.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert budget.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.budg_list', pid='budg1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == budget.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_budgets_post_put_delete(client,
                                 budget_2018_martigny,
                                 json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.budg_item', pid_value='1')
    list_url = url_for('invenio_records_rest.budg_list', q='pid:1')

    budget_2018_martigny['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.budg_list',
        budget_2018_martigny
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == budget_2018_martigny

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert budget_2018_martigny == data['metadata']

    # Update record/PUT
    data = budget_2018_martigny
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != f'"librarie.revision_id}"'

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['name'] == 'Test Name'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_budgets_can_delete(
        client, budget_2020_martigny, acq_account_fiction_martigny):
    """Test can delete an acq account."""
    can, reasons = budget_2020_martigny.can_delete
    assert not can
    assert reasons['links']['acq_accounts']
    assert reasons['others']['is_default']


def test_filtered_budgets_get(
        client, librarian_martigny, budget_2020_martigny,
        librarian_sion, budget_2020_sion):
    """Test acq accounts filter by organisation."""
    list_url = url_for('invenio_records_rest.budg_list')

    res = client.get(list_url)
    assert res.status_code == 401

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.budg_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.budg_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_budget_secure_api(client, json_header,
                           budget_2020_martigny,
                           librarian_martigny,
                           librarian_sion):
    """Test acq account secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.budg_item',
                         pid_value=budget_2020_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.budg_item',
                         pid_value=budget_2020_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_budget_secure_api_create(client, json_header,
                                  budget_2020_martigny,
                                  librarian_martigny,
                                  librarian_sion,
                                  budget_2019_martigny,
                                  system_librarian_martigny):
    """Test acq account secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.budg_list'

    del budget_2019_martigny['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        budget_2019_martigny
    )
    assert res.status_code == 403

    del budget_2020_martigny['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        budget_2020_martigny
    )
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        budget_2020_martigny
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        budget_2019_martigny
    )
    assert res.status_code == 403


def test_budget_secure_api_update(client,
                                  budget_2017_martigny,
                                  librarian_martigny,
                                  system_librarian_martigny,
                                  system_librarian_sion,
                                  librarian_sion,
                                  json_header):
    """Test acq account secure api update."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for('invenio_records_rest.budg_item',
                         pid_value=budget_2017_martigny.pid)

    data = budget_2017_martigny
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_budget_secure_api_delete(client,
                                  budget_2017_martigny,
                                  librarian_martigny,
                                  librarian_sion,
                                  system_librarian_martigny,
                                  json_header):
    """Test acq account secure api delete."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.budg_item',
                         pid_value=budget_2017_martigny.pid)

    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res = client.delete(record_url)
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.delete(record_url)
    assert res.status_code == 403
