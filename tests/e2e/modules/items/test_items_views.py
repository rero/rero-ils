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
from datetime import datetime

import pytz
from flask import url_for
from flask_security import url_for_security
from invenio_circulation.api import get_loan_for_item

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan

current_date = pytz.utc.localize(datetime.now()).isoformat()


def login_user(test_user, client):
    """Login user."""
    if test_user is not None:
        email = test_user.email
        password = test_user.password_plaintext
    return client.post(
        url_for_security('login'), data={'email': email, 'password': password}
    )


def logout_user(client):
    """Logout user."""
    client.get(url_for_security('logout'))


def test_view_automatic_checkin_multiple_loans(
    app,
    es,
    all_resources_limited,
    all_resources_limited_2,
    user_patron,
    user_staff,
    es_clear,
):
    """Test automatic_checkin multiple loans."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        loan_1 = item.loan_item(
            patron_pid=simonetta.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_LOAN
        assert get_loan_for_item(item.pid)
        assert loan_1['patron_pid'] == simonetta.pid

        new_current_date = pytz.utc.localize(datetime.now()).isoformat()

        loan_2 = item.request_item(
            patron_pid=philippe.pid,
            pickup_location_pid=location.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=philippe.pid,
            transaction_date=new_current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_LOAN
        assert item.number_of_item_requests() == 1
        assert loan_2['patron_pid'] == philippe.pid

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert 'checkin' in data.get('action_applied')
        loan_pid = data.get('action_applied').get('checkin')
        assert loan_pid == loan_1.pid
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF


def test_view_item_requested_loans_to_ignore(
    app,
    es,
    all_resources_limited,
    all_resources_limited_2,
    user_patron,
    user_staff,
    es_clear,
):
    """Test requested_loans to validate."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited

    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    loan_1 = item.request_item(
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1

    new_current_date = pytz.utc.localize(datetime.now()).isoformat()

    item.request_item(
        patron_pid=philippe.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=philippe.pid,
        transaction_date=new_current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 2

    login_user(user_staff, client)

    url = '/items/loan/requested_loans/{library_pid}'.format(
        library_pid=library.get('pid')
    )
    res = client.get(url)

    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert len(data) == 1
    assert data[0].get('patron_pid') == simonetta.pid

    loan = item.loan_item(
        loan_pid=loan_1.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert get_loan_for_item(item.pid)
    assert loan['patron_pid'] == simonetta.pid

    login_user(user_staff, client)

    url = '/items/loan/requested_loans/{library_pid}'.format(
        library_pid=library.get('pid')
    )
    res = client.get(url)

    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert len(data) == 0


def test_view_item_requested_loans_to_validate(
    app,
    es,
    all_resources_limited,
    all_resources_limited_2,
    user_patron,
    user_staff,
    es_clear,
):
    """Test requested_loans to validate."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        (
            doc2,
            item2,
            library2,
            location2,
            simonetta2,
            philippe2,
        ) = all_resources_limited_2

    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    loan_1 = item.request_item(
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1

    new_current_date = pytz.utc.localize(datetime.now()).isoformat()

    item.request_item(
        patron_pid=philippe.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=philippe.pid,
        transaction_date=new_current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 2

    login_user(user_staff, client)

    url = '/items/loan/requested_loans/{library_pid}'.format(
        library_pid=library.get('pid')
    )
    res = client.get(url)

    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert len(data) == 1
    assert data[0].get('patron_pid') == simonetta.pid

    item.cancel_item_loan(
        loan_pid=loan_1.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=new_current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1

    new_current_date = pytz.utc.localize(datetime.now()).isoformat()

    loan_1 = item.request_item(
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=new_current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 2


def test_view_automatic_checkin_missing(
    app,
    es,
    all_resources_limited,
    user_patron,
    user_staff,
    es_clear,
):
    """Test automatic_checkin item return missing."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited

        assert item.status == ItemStatus.ON_SHELF
        item.lose_item()
        assert item.status == ItemStatus.MISSING
        login_user(user_staff, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert 'return_missing' in data.get('action_applied')
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF


def test_view_automatic_checkin_receive_for_inhouse(
    app,
    es,
    all_resources_limited,
    all_resources_limited_2,
    user_patron,
    user_staff,
    es_clear,
):
    """Test automatic_checkin item receive to in-house."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        (
            doc2,
            item2,
            library2,
            location2,
            simonetta2,
            philippe2,
        ) = all_resources_limited_2

        loan = item.loan_item(
            patron_pid=simonetta.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_LOAN
        assert get_loan_for_item(item.pid)
        assert loan['patron_pid'] == simonetta.pid

        loan = item.return_item(
            patron_pid=simonetta.pid,
            loan_pid=loan.pid,
            transaction_location_pid=location2.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.IN_TRANSIT
        assert item.number_of_item_requests() == 0

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert 'receive' in data.get('action_applied')
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF


def test_view_automatic_checkin_receive_for_pickup(
    app,
    es,
    all_resources_limited,
    all_resources_limited_2,
    user_patron,
    user_staff,
    es_clear,
):
    """Test automatic_checkin item receive to pickup."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        (
            doc2,
            item2,
            library2,
            location2,
            simonetta2,
            philippe2,
        ) = all_resources_limited_2

        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 0
        loan = item.request_item(
            patron_pid=simonetta.pid,
            pickup_location_pid=location2.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 1
        assert loan['patron_pid'] == simonetta.pid
        loan = item.validate_item_request(
            loan_pid=loan.pid,
            patron_pid=simonetta.pid,
            pickup_location_pid=location2.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.IN_TRANSIT

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert 'receive' in data.get('action_applied')
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.AT_DESK


def test_view_automatic_checkin_checkin(
    app, es, all_resources_limited, user_patron, user_staff, es_clear
):
    """Test automatic_checkin item checkin."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited

        loan = item.loan_item(
            patron_pid=simonetta.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_LOAN
        assert get_loan_for_item(item.pid)
        assert loan['patron_pid'] == simonetta.pid

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert 'checkin' in data.get('action_applied')
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF


def test_view_automatic_checkin_no_actions(
    app, es, all_resources_limited, user_patron, user_staff, es_clear
):
    """Test automatic_checkin item no action."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 403
        logout_user(client)

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/automatic_checkin',
            data=json.dumps(dict(item_barcode=item.get('barcode'))),
            content_type='application/json',
        )
        assert res.status_code == 200
        assert not json.loads(res.get_data(as_text=True)).get('action_applied')


def test_view_return_item(
    app, all_resources_limited, user_staff, user_patron, es_clear
):
    """Test return items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        res = client.post(
            url_for('items.return_item'),
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 401

        login_user(user_patron, client)

        res = client.post(
            url_for('items.return_item'),
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 403
        logout_user(client)
        login_user(user_staff, client)

        loan = item.loan_item(
            patron_pid=simonetta.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_LOAN
        assert get_loan_for_item(item.pid)
        assert loan['patron_pid'] == simonetta.pid

        res = client.post(
            url_for('items.return_item'),
            data=json.dumps(dict(item_pid=item.pid, loan_pid=loan.pid)),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data.get('loan_pid') == loan.pid
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF


def test_view_validate_item(
    app, es, all_resources_limited, user_patron, user_staff, es_clear
):
    """Test return items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        res = client.post(
            '/items/loan/validate',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/loan/validate',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 403
        logout_user(client)

        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 0
        loan = item.request_item(
            patron_pid=simonetta.pid,
            pickup_location_pid=location.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 1
        assert loan['patron_pid'] == simonetta.pid
        login_user(user_staff, client)
        res = client.post(
            '/items/loan/validate',
            data=json.dumps(dict(item_pid=item.pid, loan_pid=loan.pid)),
            content_type='application/json',
        )
        assert res.status_code == 200
        assert (
            json.loads(res.get_data(as_text=True)).get('loan_pid') == loan.pid
        )
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.AT_DESK


def test_view_receive_item(
    app,
    es,
    all_resources_limited,
    all_resources_limited_2,
    user_patron,
    user_staff,
    es_clear,
):
    """Test return items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        (
            doc2,
            item2,
            library2,
            location2,
            simonetta2,
            philippe2,
        ) = all_resources_limited_2
        res = client.post(
            '/items/loan/receive',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/loan/receive',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 403
        logout_user(client)

        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 0
        loan = item.request_item(
            patron_pid=simonetta.pid,
            pickup_location_pid=location2.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 1
        assert loan['patron_pid'] == simonetta.pid
        loan = item.validate_item_request(
            loan_pid=loan.pid,
            patron_pid=simonetta.pid,
            pickup_location_pid=location2.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.IN_TRANSIT

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/receive',
            data=json.dumps(dict(item_pid=item.pid, loan_pid=loan.pid)),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data.get('loan_pid') == loan.pid
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.AT_DESK


def test_view_loan_item(
    app, es, all_resources_limited, user_patron, user_staff, es_clear
):
    """Test return items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        assert item.status == ItemStatus.ON_SHELF
        res = client.post(
            '/items/loan/checkout',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/loan/checkout',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 403
        logout_user(client)

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/checkout',
            data=json.dumps(
                dict(
                    patron_pid=simonetta.pid,
                    transaction_location_pid=location.pid,
                    transaction_user_pid=simonetta.pid,
                    transaction_date=current_date,
                    document_pid=doc.pid,
                    item_pid=item.pid,
                )
            ),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data.get('patron_pid') == simonetta.pid
        assert data.get('item_pid') == item.pid
        assert data.get('state') == 'ITEM_ON_LOAN'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_LOAN


def test_view_extend_loan(
    app, es, all_resources_limited, user_patron, user_staff, es_clear
):
    """Test return items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        assert item.status == ItemStatus.ON_SHELF
        res = client.post(
            '/items/loan/extend',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 401

        login_user(user_patron, client)
        res = client.post(
            '/items/loan/extend',
            data=json.dumps(dict(item_pid=item.pid)),
            content_type='application/json',
        )
        assert res.status_code == 403
        logout_user(client)
        loan = item.loan_item(
            patron_pid=simonetta.pid,
            transaction_location_pid=location.pid,
            transaction_user_pid=simonetta.pid,
            transaction_date=current_date,
            document_pid=doc.pid,
        )
        assert item.status == ItemStatus.ON_LOAN
        assert loan['patron_pid'] == simonetta.pid

        login_user(user_staff, client)
        res = client.post(
            '/items/loan/extend',
            data=json.dumps(
                dict(
                    patron_pid=simonetta.pid,
                    loan_pid=loan.pid,
                    transaction_location_pid=location.pid,
                    transaction_user_pid=simonetta.pid,
                    transaction_date=current_date,
                    document_pid=doc.pid,
                    item_pid=item.pid,
                )
            ),
            content_type='application/json',
        )
        assert res.status_code == 200
        data = json.loads(res.get_data(as_text=True))
        assert data.get('patron_pid') == simonetta.pid
        assert data.get('state') == 'ITEM_ON_LOAN'
        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_LOAN
        assert get_loan_for_item(item.pid)
        assert get_loan_for_item(item.pid)['extension_count'] == 1


def test_view_request_item(
    app, es, all_resources_limited, user_patron, user_staff, es_clear
):
    """Test return items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        assert item.status == ItemStatus.ON_SHELF
        url = '/items/loan/request/{item}/{location}'.format(
            item=item.pid, location=location.pid
        )
        res = client.get(url)
        assert res.status_code == 401

        login_user(user_staff, client)
        res = client.get(url)
        assert res.status_code == 403
        logout_user(client)

        assert item.number_of_item_requests() == 0

        login_user(user_patron, client)

        res = client.get(url)
        assert res.status_code == 302
        assert 'Redirecting' in res.get_data(as_text=True)

        item = Item.get_record_by_pid(item.pid)
        assert item.status == ItemStatus.ON_SHELF
        assert item.number_of_item_requests() == 1


def test_view_circulation(app, all_resources_limited, user_staff, es_clear):
    """Test circulation items using a http post request."""
    with app.test_client() as client:
        (
            doc,
            item,
            library,
            location,
            simonetta,
            philippe,
        ) = all_resources_limited
        assert item.status == ItemStatus.ON_SHELF
        res = client.get('/admin/circulation/')
        assert res.status_code == 302
        assert 'Redirecting' in res.get_data(as_text=True)

        from werkzeug.local import LocalProxy

        current_assets = LocalProxy(lambda: app.extensions['invenio-assets'])
        current_assets.collect.collect(verbose=True)
        login_user(user_staff, client)
        res = client.get('/admin/circulation/')
        assert res.status_code == 200
