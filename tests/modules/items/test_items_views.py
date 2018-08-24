# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Utils tests."""

from __future__ import absolute_import, print_function

import json

import mock

from reroils_app.modules.items.api import Item
from reroils_app.modules.items.models import ItemStatus


@mock.patch('reroils_app.modules.patrons.api.Patron.get_patron_by_email')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
@mock.patch('reroils_app.modules.patrons.listener.func_item_at_desk')
def test_view_return_item(func_item_at_desk, reindex, record_indexer,
                          get_patron_by_email, db, http_client,
                          create_minimal_resources
                          ):
    """Test return items using a http post request."""
    # hack the return value
    get_patron_by_email.return_value = {'member_pid': '1'}

    res = http_client.post('/items/return',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.post('/items/return',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 403
    http_client.get('/test/logout')
    doc, item, member, location = create_minimal_resources

    assert item.status == ItemStatus.ON_LOAN

    res = http_client.get('/test/login?role=cataloguer')

    res = http_client.post('/items/return',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.AT_DESK


@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
@mock.patch('reroils_app.modules.patrons.listener.func_item_at_desk')
def test_view_validate_item(func_item_at_desk, reindex, record_indexer,
                            db, http_client,
                            create_minimal_resources_on_shelf_req):
    """Test return items using a http post request."""
    res = http_client.post('/items/validate',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.post('/items/validate',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 403
    http_client.get('/test/logout')

    doc, item, member, location = create_minimal_resources_on_shelf_req

    assert item.status == ItemStatus.ON_SHELF

    res = http_client.get('/test/login?role=cataloguer')

    res = http_client.post('/items/validate',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.AT_DESK


@mock.patch('reroils_app.modules.patrons.api.Patron.get_patron_by_email')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
def test_view_receive_item(reindex, record_indexer,
                           get_patron_by_email, db, http_client,
                           create_minimal_resources_in_transit):
    """Test return items using a http post request."""
    # hack the return value
    get_patron_by_email.return_value = {'member_pid': '1'}

    res = http_client.post('/items/receive',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.post('/items/receive',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 403
    http_client.get('/test/logout')

    doc, item, member, location = create_minimal_resources_in_transit
    assert item.status == ItemStatus.IN_TRANSIT

    res = http_client.get('/test/login?role=cataloguer')

    res = http_client.post('/items/receive',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF


@mock.patch('reroils_app.modules.patrons.api.Patron.get_patron_by_email')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
def test_view_loan_item(reindex, record_indexer,
                        get_patron_by_email, db, http_client,
                        create_minimal_resources_on_shelf):
    """Test return items using a http post request."""
    # hack the return value
    get_patron_by_email.return_value = {'member_pid': '1'}

    res = http_client.post('/items/loan',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.post('/items/loan',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 403
    http_client.get('/test/logout')

    doc, item, member, location = create_minimal_resources_on_shelf
    assert item.status == ItemStatus.ON_SHELF

    res = http_client.get('/test/login?role=cataloguer')

    res = http_client.post('/items/loan',
                           data=json.dumps(dict(
                               pid='1',
                               patron_barcode='12345678',
                               start_date='2018-01-01',
                               end_date='2018-02-01'
                           )), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_LOAN


@mock.patch('reroils_app.modules.patrons.api.Patron.get_patron_by_email')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
def test_view_extend_loan(reindex, record_indexer,
                          get_patron_by_email, db, http_client,
                          create_minimal_resources_on_loan):
    """Test return items using a http post request."""
    # hack the return value
    get_patron_by_email.return_value = {'member_pid': '1'}

    res = http_client.post('/items/extend',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.post('/items/extend',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 403
    http_client.get('/test/logout')

    doc, item, member, location = create_minimal_resources_on_loan
    assert item.status == ItemStatus.ON_LOAN

    res = http_client.get('/test/login?role=cataloguer')

    res = http_client.post('/items/extend',
                           data=json.dumps(dict(
                               pid='1'
                           )), content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_LOAN
    assert item['_circulation']['holdings'][0]['renewal_count'] == 1


@mock.patch('reroils_app.modules.patrons.api.Patron.get_patron_by_email')
@mock.patch('invenio_indexer.api.RecordIndexer')
@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
@mock.patch('reroils_app.modules.items.views.url_for')
def test_view_request_item(url_for, reindex, record_indexer,
                           get_patron_by_email,
                           db, http_client,
                           create_minimal_resources_on_shelf,
                           minimal_patron_record):
    """Test return items using a http post request."""
    # hack the return value
    minimal_patron_record['email'] = 'test@rero.ch'
    get_patron_by_email.return_value = minimal_patron_record

    res = http_client.get('/items/request/1/1')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.get('/items/request/1/1')
    assert res.status_code == 403
    http_client.get('/test/logout')

    doc, item, member, location = create_minimal_resources_on_shelf

    db.session.commit()
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0

    res = http_client.get('/test/login?role=patrons')

    res = http_client.get('/items/request/1/1')
    assert res.status_code == 302
    assert 'Redirecting' in res.get_data(as_text=True)

    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1


@mock.patch('reroils_app.modules.items.views.render_template')
def test_view_circulation(render_template, minimal_patron_record,
                          db, http_client):
    """Test circulation items using a http post request."""
    # hack the return value
    render_template.return_value = 'hello world'

    res = http_client.get('/items/circulation')
    assert res.status_code == 401

    res = http_client.get('/test/login')
    res = http_client.get('/items/circulation')
    assert res.status_code == 403
    http_client.get('/test/logout')

    res = http_client.get('/test/login?role=patrons')
    res = http_client.get('/items/circulation')
    assert res.status_code == 403
    http_client.get('/test/logout')

    res = http_client.get('/test/login?role=cataloguer')

    res = http_client.get('/items/circulation')
    assert res.status_code == 200
