#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Tests Serializers."""


import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_circ_policies(
    client,
    org_martigny,
    circ_policy_default_martigny,
    can_delete_json_header,
    json_header
):
    """Test record retrieval."""
    item_url = url_for(
        'invenio_records_rest.cipo_item',
        pid_value='cipo1'
    )

    res = client.get(item_url, headers=can_delete_json_header)

    assert res.status_code == 200
    data = get_json(res)['metadata']
    assert 'cannot_delete' in data
    assert data.get('cannot_delete') == {'others': {'is_default': True}}

    res = client.get(item_url, headers=json_header)

    assert res.status_code == 200
    assert 'cannot_delete' not in get_json(res)['metadata']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents(
    client,
    document,
    item_lib_martigny,
    can_delete_json_header,
    json_header
):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.doc_item', pid_value='doc1')

    res = client.get(item_url, headers=can_delete_json_header)
    assert res.status_code == 200

    data = get_json(res)['metadata']
    assert 'cannot_delete' in data
    assert data.get('cannot_delete') == {'links': {'items': 1}}

    res = client.get(item_url, headers=json_header)
    assert res.status_code == 200
    assert 'cannot_delete' not in get_json(res)['metadata']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_item_types(
    client,
    item_type_standard_martigny,
    can_delete_json_header,
    json_header
):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.itty_item', pid_value='itty1')

    res = client.get(item_url, headers=can_delete_json_header)
    assert res.status_code == 200

    data = get_json(res)['metadata']
    assert 'cannot_delete' in data
    assert data.get('cannot_delete') == {'links': {'items': 1}}

    res = client.get(item_url, headers=json_header)
    assert res.status_code == 200
    assert 'cannot_delete' not in get_json(res)['metadata']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_items(
    client,
    item_lib_martigny,
    json_header,
    can_delete_json_header
):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.item_item', pid_value='item1')

    res = client.get(item_url, headers=can_delete_json_header)
    assert res.status_code == 200

    assert 'cannot_delete' not in get_json(res)['metadata']
