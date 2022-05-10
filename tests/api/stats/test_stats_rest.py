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

"""Tests REST API item types."""


import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_csv, get_json, postdata, \
    to_relative_url


def test_stats_permissions(client, stats):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.stat_item', pid_value=stats.pid)
    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.stat_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.stat_item', pid_value=stats.pid),
        data={}
    )
    assert res.status_code == 401

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_stats_get(client, stats, csv_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.stat_item', pid_value=stats.pid)
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag']

    data = get_json(res)

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200

    # CSV format
    item_url = url_for(
        'invenio_records_rest.stat_item', pid_value=stats.pid, format='csv')
    res = client.get(item_url, headers=csv_header)
    assert res.status_code == 200

    data = get_csv(res)
    assert data == (
        'library id,library name,number_of_active_patrons,'
        'number_of_checkins,number_of_checkouts,'
        'number_of_deleted_items,number_of_documents,'
        'number_of_items,number_of_librarians,number_of_libraries,'
        'number_of_new_items,number_of_new_patrons,'
        'number_of_order_lines,number_of_patrons,'
        'number_of_renewals,number_of_requests,'
        'number_of_satisfied_ill_request\r\n'
        'lib3,Library of Fully,0,0,0,0,1,1,0,2,1,1,0,1,0,0,0\r\n'
        'lib1,Library of Martigny-ville,0,0,0,0,1,1,0,2,1,1,0,1,0,0,1\r\n'
        'lib4,Library of Sion,0,0,0,0,1,1,0,1,1,0,0,0,0,0,0\r\n'
    )

    list_url = url_for('invenio_records_rest.stat_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['hits']


def test_stats_get_post_put_delete(client, librarian_martigny):
    """Test CRUD operations."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.stat_item', pid_value='1')
    list_url = url_for('invenio_records_rest.stat_list', q='pid:1')

    login_user_via_session(client, librarian_martigny.user)

    # GET is not allowed for a librarian or system librarian
    res = client.get(item_url)
    assert res.status_code == 403

    res, data = postdata(
        client,
        'invenio_records_rest.stat_list',
        {}
    )
    assert res.status_code == 403

    # Update record/PUT
    res = client.put(
        item_url,
        data={}
    )
    assert res.status_code == 403

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 403


def test_stats_librarian_permissions(client, stats_librarian):
    """Test record retrieval for statistics librarian."""
    item_url = url_for('invenio_records_rest.stat_item',
                       pid_value=stats_librarian.pid)
    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.stat_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.stat_item',
                pid_value=stats_librarian.pid),
        data={}
    )
    assert res.status_code == 401

    res = client.delete(item_url)
    assert res.status_code == 401


def test_stats_librarian_get_post_put_delete(client, stats_librarian,
                                             librarian_martigny,
                                             librarian_sion,
                                             patron_martigny):
    """Test CRUD operations for statistics librarian."""
    # patron: role librarian
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for('invenio_records_rest.stat_item',
                       pid_value=stats_librarian.pid)

    # GET is allowed for a librarian or system librarian
    res = client.get(item_url)
    assert res.status_code == 200

    # POST / Create record
    res, data = postdata(
        client,
        'invenio_records_rest.stat_list',
        {}
    )
    assert res.status_code == 403

    # PUT / Update record
    res = client.put(
        item_url,
        data={}
    )
    assert res.status_code == 403

    # DELETE / Delete record
    res = client.delete(item_url)
    assert res.status_code == 403

    # patron: role patron
    login_user_via_session(client, patron_martigny.user)

    # GET is not allowed for a patron
    res = client.get(item_url)
    assert res.status_code == 403

    # POST / Create record
    res, data = postdata(
        client,
        'invenio_records_rest.stat_list',
        {}
    )
    assert res.status_code == 403

    # PUT / Update record
    res = client.put(
        item_url,
        data={}
    )
    assert res.status_code == 403

    # DELETE / Delete record
    res = client.delete(item_url)
    assert res.status_code == 403


def test_stats_librarian_data(client, stats_librarian, librarian_martigny):
    """Check data include date_range and type librarian."""
    login_user_via_session(client, librarian_martigny.user)

    item_url = url_for('invenio_records_rest.stat_item',
                       pid_value=stats_librarian.pid)
    res = client.get(item_url)
    data = res.get_json()

    assert data['metadata']['date_range']
    assert data['metadata']['type'] == 'librarian'
