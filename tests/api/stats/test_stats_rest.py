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

"""Tests statistics REST API."""

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_csv, get_json, \
    to_relative_url


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_stats_get(client, stats, csv_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.stat_item', pid_value=stats.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag']
    data = get_json(res)
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200

    # CSV format
    params = {'pid_value': stats.pid, 'format': 'csv'}
    item_url = url_for('invenio_records_rest.stat_item', **params)
    res = client.get(item_url, headers=csv_header)
    assert res.status_code == 200
    data = get_csv(res)
    assert data == (
        'library id,library name,number_of_active_patrons,'
        'number_of_checkins,number_of_checkouts,'
        'number_of_deleted_items,number_of_documents,'
        'number_of_ill_requests,number_of_items,number_of_librarians,'
        'number_of_libraries,number_of_new_items,number_of_new_patrons,'
        'number_of_order_lines,number_of_patrons,'
        'number_of_renewals,number_of_requests\r\n'
        'lib3,Library of Fully,0,0,0,0,1,0,1,0,2,1,1,0,1,0,0\r\n'
        'lib1,Library of Martigny-ville,0,0,0,0,1,1,1,0,2,1,1,0,1,0,0\r\n'
        'lib4,Library of Sion,0,0,0,0,1,0,1,0,1,1,0,0,0,0,0\r\n'
    )

    list_url = url_for('invenio_records_rest.stat_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['hits']


def test_stats_librarian_data(
    client, stats_librarian, librarian_martigny, system_librarian_martigny
):
    """Test librarian statistics."""
    params = dict(pid_value=stats_librarian.pid)
    item_url = url_for('invenio_records_rest.stat_item', **params)

    # system librarian could view all libraries stats for its own organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(item_url)
    data = res.get_json()
    filtered_stat_libs = {
        value['library']['pid'] for value in data['metadata']['values']
    }
    manageable_libs = set(system_librarian_martigny.manageable_library_pids)

    assert not filtered_stat_libs.difference(manageable_libs)

    # Check filtered librarian stats by libraries
    librarian_martigny['roles'].append('pro_statistic_manager')
    librarian_martigny.update(
        librarian_martigny, dbcommit=False, reindex=False)
    login_user_via_session(client, librarian_martigny.user)

    res = client.get(item_url)
    data = res.get_json()

    # Check response contains 'date_range' and 'librarian'
    assert data['metadata']['date_range']
    assert data['metadata']['type'] == 'librarian'

    # Check that response contains only stats for the manageable libraries.
    # This filter is applied by the 'pre_dump' resource extension
    manageable_libs = set(librarian_martigny.manageable_library_pids)
    initial_stat_libs = {
        value['library']['pid'] for value in stats_librarian['values']
    }
    filtered_stat_libs = {
        value['library']['pid'] for value in data['metadata']['values']
    }
    assert initial_stat_libs.difference(manageable_libs)
    assert not filtered_stat_libs.difference(manageable_libs)
    from invenio_db import db
    db.session.rollback()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_stats_report_get(client, stats_report_martigny, csv_header):
    """Test record retrieval."""
    item_url = url_for(
        'invenio_records_rest.stat_item', pid_value=stats_report_martigny.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag']
    data = get_json(res)
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data
    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200

    # CSV format
    params = {'pid_value': stats_report_martigny.pid, 'format': 'csv'}
    item_url = url_for('invenio_records_rest.stat_item', **params)
    res = client.get(item_url, headers=csv_header)
    assert res.status_code == 200
    data = get_csv(res)
    assert data
    list_url = url_for('invenio_records_rest.stat_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['hits']
