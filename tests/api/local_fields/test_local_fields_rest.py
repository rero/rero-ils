# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Tests REST API local fields."""

import json
from copy import deepcopy

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, flush_index, get_json, postdata

from rero_ils.modules.local_fields.api import LocalFieldsSearch


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_local_fields_get(client, local_field_martigny):
    """Test GET on local fields."""
    local_fields_url = url_for(
        'invenio_records_rest.lofi_item',
        pid_value=local_field_martigny.pid
    )
    res = client.get(local_fields_url)
    assert res.status_code == 200
    data = get_json(res)
    assert local_field_martigny == data['metadata']

    list_url = url_for(
        'invenio_records_rest.lofi_list',
        pid=local_field_martigny.pid
    )
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['hits'][0]['metadata'] == \
        local_field_martigny.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_local_fields_post_put_delete(client, org_sion, document,
                                      local_field_sion_data, json_header):
    """Test POST and PUT on local fields."""
    lf_pid = local_field_sion_data['pid']
    item_url = url_for('invenio_records_rest.lofi_item', pid_value=lf_pid)
    list_url = url_for('invenio_records_rest.lofi_list', q=f'pid:{lf_pid}')

    res, data = postdata(client, 'invenio_records_rest.lofi_list',
                         local_field_sion_data)
    assert res.status_code == 201
    assert data['metadata'] == local_field_sion_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert local_field_sion_data == data['metadata']

    new_lofi = deepcopy(local_field_sion_data)
    new_lofi['fields']['field_2'] = ['field 2']
    res = client.put(
        item_url,
        data=json.dumps(new_lofi),
        headers=json_header
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data['metadata']['fields']['field_2'][0] == 'field 2'

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['fields']['field_2'][0] == 'field 2'

    # Check duplicate record
    flush_index(LocalFieldsSearch.Meta.index)
    del new_lofi['pid']
    res, _ = postdata(client, 'invenio_records_rest.lofi_list', new_lofi)
    assert res.status_code == 400

    res = client.get(url_for(
        'invenio_records_rest.lofi_list',
        q=f'organisation.pid:{data["metadata"]["organisation"]["pid"]}'
    ))
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Delete record
    res = client.delete(item_url)
    assert res.status_code == 204
    res = client.get(item_url)
    assert res.status_code == 410
