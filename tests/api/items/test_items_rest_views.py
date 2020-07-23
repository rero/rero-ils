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

"""Tests REST API items."""
import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.items.api import Item


def test_item_dumps(client, item_lib_martigny, org_martigny,
                    librarian_martigny_no_email):
    """Test item dumps and elastic search version."""
    item_dumps = Item(item_lib_martigny.dumps()).replace_refs()

    assert item_dumps.get('available')
    assert item_dumps.get('organisation').get('pid') == org_martigny.pid

    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    item_es = Item(get_json(res).get('metadata'))
    assert item_es.available
    assert item_es.organisation_pid == org_martigny.pid


def test_item_secure_api(client, json_header, item_lib_martigny,
                         librarian_martigny_no_email, librarian_sion_no_email,
                         loc_public_saxon):
    """Test item secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)
    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200


def test_item_secure_api_create(client, json_header, item_lib_martigny,
                                librarian_martigny_no_email,
                                librarian_sion_no_email,
                                item_lib_martigny_data,
                                item_lib_saxon_data,
                                system_librarian_martigny_no_email):
    """Test item secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = 'invenio_records_rest.item_list'

    del item_lib_martigny_data['pid']
    res, _ = postdata(
        client,
        post_url,
        item_lib_martigny_data
    )
    # librarian can create items on its affilicated library
    assert res.status_code == 201

    del item_lib_saxon_data['pid']
    res, _ = postdata(
        client,
        post_url,
        item_lib_saxon_data
    )
    # librarian can not create items for another library
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        post_url,
        item_lib_saxon_data
    )
    # sys_librarian can create items for any library
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res, _ = postdata(
        client,
        post_url,
        item_lib_martigny_data
    )
    # librarian can not create items in another organisation
    assert res.status_code == 403


def test_item_secure_api_update(client, json_header, item_lib_saxon,
                                librarian_martigny_no_email,
                                librarian_sion_no_email,
                                item_lib_martigny,
                                system_librarian_martigny_no_email
                                ):
    """Test item secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)

    item_lib_martigny['call_number'] = 'call_number'
    res = client.put(
        record_url,
        data=json.dumps(item_lib_martigny),
        headers=json_header
    )
    # librarian can update items of its affiliated library
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_saxon.pid)

    item_lib_saxon['call_number'] = 'call_number'
    res = client.put(
        record_url,
        data=json.dumps(item_lib_saxon),
        headers=json_header
    )
    # librarian can not update items of other libraries
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.put(
        record_url,
        data=json.dumps(item_lib_saxon),
        headers=json_header
    )
    # sys_librarian can update items of other libraries in same organisation.
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(item_lib_saxon),
        headers=json_header
    )
    # librarian can not update items of other libraries in other organisation.
    assert res.status_code == 403


def test_item_secure_api_delete(client, item_lib_saxon,
                                librarian_martigny_no_email,
                                librarian_sion_no_email,
                                item_lib_martigny,
                                json_header,
                                system_librarian_martigny_no_email):
    """Test item secure api delete."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_martigny.pid)

    res = client.delete(record_url)
    # librarian can delete items of its affiliated library
    assert res.status_code == 204

    record_url = url_for('invenio_records_rest.item_item',
                         pid_value=item_lib_saxon.pid)

    res = client.delete(record_url)
    # librarian can not delete items of other libraries
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.delete(record_url)
    # librarian can not delete items of other organisations
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.delete(record_url)
    # sys_librarian can delete items in other libraries in same org.
    assert res.status_code == 204


def test_pending_loans_order(client, librarian_martigny_no_email,
                             patron_martigny_no_email, loc_public_martigny,
                             item_type_standard_martigny,
                             item2_lib_martigny, json_header,
                             patron2_martigny_no_email, patron_sion_no_email,
                             circulation_policies):
    """Test sort of pending loans."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    library_pid = librarian_martigny_no_email.replace_refs()['library']['pid']

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_sion_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    # sort by pid asc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='pid'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[2]['pid'] > loans[1]['pid'] > loans[0]['pid']

    # sort by pid desc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='-pid'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[2]['pid'] < loans[1]['pid'] < loans[0]['pid']

    # sort by transaction desc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='-transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[2]['pid'] < loans[1]['pid'] < loans[0]['pid']

    # sort by patron_pid asc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='patron_pid'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[0]['patron_pid'] == patron_sion_no_email.pid
    assert loans[1]['patron_pid'] == patron_martigny_no_email.pid
    assert loans[2]['patron_pid'] == patron2_martigny_no_email.pid

    # sort by invalid field
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='does not exist'))
    assert res.status_code == 500
    data = get_json(res)
    assert 'RequestError(400' in data['status']


def test_patron_checkouts_order(client, librarian_martigny_no_email,
                                patron_martigny_no_email, loc_public_martigny,
                                item_type_standard_martigny,
                                item3_lib_martigny, json_header,
                                item4_lib_martigny,
                                circulation_policies):
    """Test sort of checkout loans."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item4_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    # sort by transaction_date asc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny_no_email.pid,
            sort='transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item3_lib_martigny.pid
    assert items[1]['item']['pid'] == item4_lib_martigny.pid

    # sort by transaction_date desc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny_no_email.pid,
            sort='-transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item4_lib_martigny.pid
    assert items[1]['item']['pid'] == item3_lib_martigny.pid

    # sort by invalid field
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny_no_email.pid,
            sort='does not exist'))
    assert res.status_code == 500
    data = get_json(res)
    assert 'RequestError(400' in data['status']
