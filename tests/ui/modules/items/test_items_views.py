# -*- coding: utf-8 -*-
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

"""Utils tests."""

from __future__ import absolute_import, print_function

import json

from flask import url_for
from flask_security import url_for_security

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus


def login_user(test_user, client):
    """Login user."""
    if test_user is not None:
        email = test_user.email
        password = test_user.password_plaintext
    return client.post(
        url_for_security('login'),
        data={'email': email, 'password': password}
    )


def logout_user(client):
    """Logout user."""
    client.get(
        url_for_security('logout')
    )


# def test_es(app, es, minimal_member_record):
#     """test es."""
#     from rero_ils.modules.members.api import Member, MembersSearch
#     member = Member.create(
#         minimal_member_record,
#         dbcommit=True,
#         reindex=True
#     )
#     es_flush_and_refresh()
#
#     assert list(MembersSearch().filter("match_all").source().scan()) != []


def test_view_return_item(app, es, user_patron,  user_staff,
                          create_minimal_resources):
    """Test return items using a http post request."""
    with app.test_client() as client:
        res = client.post(
            url_for('items.return_item'),
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 401

        login_user(user_patron, client)

        res = client.post(
            url_for('items.return_item'),
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 403
        logout_user(client)
        login_user(user_staff, client)

        doc, item, member, location = create_minimal_resources
        assert item.status == ItemStatus.ON_LOAN

        res = client.post(
            url_for('items.return_item'),
            data=json.dumps(dict(pid=item.pid)),
            content_type='application/json'
        )
        assert res.status_code == 200
        assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.AT_DESK


def test_view_validate_item(app, es, user_patron, user_staff,
                            create_minimal_resources_on_shelf_req):
    """Test return items using a http post request."""
    with app.test_client() as client:
        res = client.post(
            '/items/validate',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/validate',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 403
        logout_user(client)

        doc, item, member, location = create_minimal_resources_on_shelf_req
        assert item.status == ItemStatus.ON_SHELF

        login_user(user_staff, client)
        res = client.post(
            '/items/validate',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 200
        assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.AT_DESK


def test_view_receive_item(app, es, user_patron, user_staff,
                           create_minimal_resources_in_transit):
    """Test return items using a http post request."""
    with app.test_client() as client:
        res = client.post(
            '/items/receive',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/receive',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 403
        logout_user(client)

        doc, item, member, location = create_minimal_resources_in_transit
        assert item.status == ItemStatus.IN_TRANSIT

        login_user(user_staff, client)
        res = client.post(
            '/items/receive',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 200
        assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF


def test_view_loan_item(app, es, user_patron, user_staff,
                        create_minimal_resources_on_shelf):
    """Test return items using a http post request."""
    with app.test_client() as client:
        res = client.post(
            '/items/loan',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/loan',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 403
        logout_user(client)

        doc, item, member, location = create_minimal_resources_on_shelf
        assert item.status == ItemStatus.ON_SHELF

        login_user(user_staff, client)
        res = client.post(
            '/items/loan',
            data=json.dumps(dict(
                pid='1',
                patron_barcode='12345678',
                start_date='2018-01-01',
                end_date='2018-02-01'
            )),
            content_type='application/json'
        )
        assert res.status_code == 200
        assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_LOAN


def test_view_extend_loan(app, es, user_patron, user_staff,
                          create_minimal_resources_on_loan):
    """Test return items using a http post request."""
    with app.test_client() as client:
        res = client.post(
            '/items/extend',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/extend',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 403
        logout_user(client)

        doc, item, member, location = create_minimal_resources_on_loan
        assert item.status == ItemStatus.ON_LOAN

        login_user(user_staff, client)
        res = client.post(
            '/items/extend',
            data=json.dumps(dict(pid='1')),
            content_type='application/json'
        )
        assert res.status_code == 200
        assert json.loads(res.get_data(as_text=True)).get('status') == 'ok'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_LOAN
        assert item['_circulation']['holdings'][0]['renewal_count'] == 1


def test_view_request_item(app, es, user_patron, user_staff,
                           create_minimal_resources_on_shelf,
                           minimal_patron_record):
    """Test return items using a http post request."""
    with app.test_client() as client:
        res = client.get('/items/request/1/1')
        assert res.status_code == 401

        login_user(user_staff, client)
        res = client.get('/items/request/1/1')
        assert res.status_code == 403
        logout_user(client)

        doc, item, member, location = create_minimal_resources_on_shelf
        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 0

        login_user(user_patron, client)

        res = client.get('/items/request/1/1')
        assert res.status_code == 302
        assert 'Redirecting' in res.get_data(as_text=True)

        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 1


def test_view_circulation(app, user_staff, minimal_patron_record):
    """Test circulation items using a http post request."""

    with app.test_client() as client:
        res = client.get('/admin/circulation/')
        assert res.status_code == 302
        assert 'Redirecting' in res.get_data(as_text=True)

        login_user(user_staff, client)
        res = client.get('/admin/circulation/')
        assert res.status_code == 200
