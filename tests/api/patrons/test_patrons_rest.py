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

"""Tests REST API patrons."""

import json
from copy import deepcopy
from datetime import datetime, timedelta

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, create_patron, get_json, \
    postdata, to_relative_url

from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import extracted_data_from_ref, get_ref_for_pid
from rero_ils.utils import create_user_from_data


def test_patrons_shortcuts(
        client, librarian_martigny, patron_martigny,
        librarian_sion):
    """Test patron shortcuts."""
    new_patron = deepcopy(patron_martigny)
    assert new_patron.patron_type_pid
    assert new_patron.organisation_pid
    del new_patron['patron']['type']
    assert not new_patron.patron_type_pid
    assert not new_patron.organisation_pid
    assert new_patron.formatted_name == "Roduit, Louis"


def test_filtered_patrons_get(
        client, librarian_martigny, patron_martigny,
        librarian_sion):
    """Test patron filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.ptrn_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # Sion
    # TODO: find why it's failed
    # login_user_via_session(client, librarian_sion.user)
    # list_url = url_for('invenio_records_rest.ptrn_list')

    # res = client.get(list_url)
    # assert res.status_code == 200
    # data = get_json(res)
    # assert data['hits']['total']['value'] == 1

def test_patron_has_valid_subscriptions(
        patron_type_grown_sion, patron_sion, patron_sion_data,
        patron_type_adults_martigny, patron2_martigny,
        patron_type_youngsters_sion):
    """Test patron subscriptions."""
    patron_sion = patron_sion
    patron_martigny = patron2_martigny

    # 'patron_type_adults_martigny' doesn't require any subscription
    # 'patron2_martigny' is linked to it, so `has_valid_subscription`
    # should return True
    assert not patron_type_adults_martigny.is_subscription_required
    assert patron_martigny.has_valid_subscription

    # 'patron_type_grown_sion' require a subscription
    # removed all stored subscription and test if subscription exists
    if patron_sion.get('patron', {}).get('subscriptions'):
        del patron_sion['patron']['subscriptions']
    assert patron_type_grown_sion.is_subscription_required
    assert not patron_sion.has_valid_subscription

    # Create a subscription for this patron and check this subscription is
    # stored and valid
    start = datetime.now() - timedelta(seconds=10)
    end = datetime.now() + timedelta(days=10)
    patron_sion.add_subscription(patron_type_grown_sion, start, end)
    assert patron_sion.has_valid_subscription
    assert len(patron_sion.get_valid_subscriptions()) == 1
    subscription = patron_sion.get_valid_subscriptions()[0]
    assert subscription.get('start_date') == start.strftime('%Y-%m-%d')

    # Create a old subscription for this patron and check validity
    start = datetime.now() - timedelta(days=20)
    end = start + timedelta(days=10)
    patron_sion.add_subscription(patron_type_grown_sion, start, end)
    assert len(patron_sion.get('patron', {}).get('subscriptions', [])) == 2
    assert len(patron_sion.get_valid_subscriptions()) == 1

    # remove old subscriptions. Create an old one and check the patron doesn't
    # have any valid subscription
    del patron_sion['patron']['subscriptions']
    patron_sion.add_subscription(patron_type_grown_sion, start, end)
    # !! As `add_subscription` use the method `Patron.update`, then the signal
    #    `after_record_update` are send by invenio_records and the patron
    #    listener `create_subscription_patron_transaction` is called. This
    #    listener found that user doesn't have any subscription and add a valid
    #    one for this patron. So after `add_subscription` call, I just removed
    #    the valid subscription created.
    del patron_sion['patron']['subscriptions'][1]
    assert not patron_sion.has_valid_subscription

    # remove all subscriptions. Create a valid subscription other patron_type
    # than current patron.patron_type. Check if the patron has a valid
    # subscription
    del patron_sion['patron']['subscriptions']
    start = datetime.now() - timedelta(seconds=10)
    end = datetime.now() + timedelta(days=10)
    patron_sion.add_subscription(patron_type_youngsters_sion, start, end)
    assert patron_sion.has_valid_subscription

    # Create a old subscription for `patron_sion`. Call ES to know patrons with
    # an obsolete subscription. This query should return the recently updated
    # patron.
    start = datetime.now() - timedelta(days=20)
    end = start + timedelta(days=10)
    patron_sion.add_subscription(patron_type_youngsters_sion, start, end)
    patron_sion.add_subscription(patron_type_grown_sion, start, end)
    patrons = list(Patron.patrons_with_obsolete_subscription_pids())
    assert len(patrons) == 1 and patrons[0].pid == patron_sion.pid
    # same check for a very old end_date
    end_date = end - timedelta(days=100)
    patrons = list(Patron.patrons_with_obsolete_subscription_pids(end_date))
    assert len(patrons) == 0

    # Reset the patron as at the beginning
    del patron_sion['patron']['subscriptions']
    start = datetime.now()
    end = datetime.now() + timedelta(days=10)
    patron_sion.add_subscription(patron_type_grown_sion, start, end)


def test_patron_pending_subscription(client, patron_type_grown_sion,
                                     patron_sion,
                                     librarian_sion,
                                     patron_transaction_overdue_event_martigny,
                                     lib_sion):
    """Test get pending subscription for patron."""
    # At the beginning, `patron_sion` should have one pending
    # subscription.
    pending_subscription = patron_sion.get_pending_subscriptions()
    assert len(pending_subscription) == 1

    # Pay this subscription.
    login_user_via_session(client, librarian_sion.user)
    post_entrypoint = 'invenio_records_rest.ptre_list'
    trans_pid = extracted_data_from_ref(
        pending_subscription[0]['patron_transaction'], data='pid'
    )
    transaction = PatronTransaction.get_record_by_pid(trans_pid)
    payment = deepcopy(patron_transaction_overdue_event_martigny)
    del payment['pid']
    payment['type'] = 'payment'
    payment['subtype'] = 'cash'
    payment['amount'] = transaction.total_amount
    payment['operator'] = {
        '$ref': get_ref_for_pid(
            'patrons', librarian_sion.pid
        )
    }
    payment['library'] = {
        '$ref': get_ref_for_pid('libraries', lib_sion.pid)
    }
    payment['parent'] = pending_subscription[0]['patron_transaction']
    res, _ = postdata(client, post_entrypoint, payment)
    assert res.status_code == 201
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert transaction.status == 'closed'

    # reload the patron and check the pending subscription. As we paid the
    # previous subscription, there will be none pending subscription
    patron_sion = Patron.get_record_by_pid(patron_sion.pid)
    pending_subscription = patron_sion.get_pending_subscriptions()
    assert len(pending_subscription) == 0


def test_patrons_permissions(client, librarian_martigny,
                             json_header):
    """Test record retrieval."""
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian_martigny.pid)

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.ptrn_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        item_url,
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401

@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patrons_get(client, librarian_martigny):
    """Test record retrieval."""
    patron = librarian_martigny
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian_martigny.pid)
    list_url = url_for(
        'invenio_records_rest.ptrn_list',
        q='pid:{pid}'.format(pid=librarian_martigny.pid))

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(patron.revision_id)

    data = get_json(res)
    assert patron.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert patron.dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    result = data['hits']['hits'][0]['metadata']
    # organisation has been added during the indexing
    del(result['organisation'])
    assert result == patron.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patrons_post_put_delete(app, client, lib_martigny,
                                 patron_type_children_martigny,
                                 patron_martigny_data_tmp, json_header,
                                 roles, mailbox):
    """Test record retrieval."""
    pid_value = 'ptrn_1'
    item_url = url_for('invenio_records_rest.ptrn_item', pid_value=pid_value)
    list_url = url_for(
        'invenio_records_rest.ptrn_list', q='pid:%s' % pid_value)
    patron_data = deepcopy(patron_martigny_data_tmp)
    patron_data['email'] = 'post_put_delete@test.ch'
    patron_data['username'] = 'post_put_delete'
    patron_data = create_user_from_data(patron_data)

    pids = Patron.count()
    assert len(mailbox) == 0

    # Create record / POST
    patron_data['pid'] = pid_value
    # patron_data['email'] = 'test_librarian@rero.ch'
    # patron_data['username'] = 'test_librarian'

    res, _ = postdata(
        client,
        'invenio_records_rest.ptrn_list',
        patron_data
    )

    assert res.status_code == 201
    assert Patron.count() == pids + 1
    # assert len(mailbox) == 1
    # assert re.search(r'localhost/lost-password', mailbox[0].body)

    # # Check that the returned record matches the given data
    # data = get_json(res)
    # # remove dynamic property
    # del data['metadata']['user_id']
    # assert data['metadata'] == patron_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    # add dynamic property
    patron_data['user_id'] = data['metadata']['user_id']
    data['metadata']['user_id']

    # Update record/PUT
    data = patron_data
    data['patron']['barcode'] = 'barcode_test'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(ptrnrarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['patron']['barcode']  == 'barcode_test'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['patron']['barcode']  == 'barcode_test'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['patron']['barcode']  == 'barcode_test'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410
    ds = app.extensions['invenio-accounts'].datastore
    ds.delete_user(ds.find_user(id=patron_data['user_id']))


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patrons_post_without_email(app, client, lib_martigny,
                                    patron_type_children_martigny,
                                    patron_martigny_data_tmp, json_header,
                                    roles, mailbox):
    """Test record retrieval."""
    patron_data = deepcopy(patron_martigny_data_tmp)
    patron_data['email'] = 'post_without_email@test.ch'
    patron_data['username'] = 'post_without_email'
    patron_data = create_user_from_data(patron_data)

    pids = Patron.count()
    assert len(mailbox) == 0

    # Create record / POST
    del patron_data['pid']
    del patron_data['email']
    patron_data['patron']['communication_channel'] = 'mail'

    res, _ = postdata(
        client,
        'invenio_records_rest.ptrn_list',
        patron_data
    )

    assert res.status_code == 201
    assert Patron.count() == pids + 1
    assert len(mailbox) == 0

    # Check that the returned record matches the given data
    data = get_json(res)
    data['metadata']['patron']['communication_channel'] = 'mail'

    ds = app.extensions['invenio-accounts'].datastore
    ds.delete_user(ds.find_user(id=patron_data['user_id']))


def test_patron_secure_api(client, json_header,
                           librarian_martigny,
                           librarian_sion):
    """Test patron type secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=librarian_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=librarian_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_patron_secure_api_create(client, patron_type_children_martigny,
                                  patron_martigny_data,
                                  librarian_martigny,
                                  librarian_sion):
    """Test patron secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.ptrn_list'

    del patron_martigny_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_martigny_data
    )
    assert res.status_code == 201

    # # Sion
    login_user_via_session(client, librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        patron_martigny_data
    )
    assert res.status_code == 403


def test_patron_secure_api_delete(app, client, librarian_martigny,
                                  librarian_sion,
                                  roles,
                                  lib_martigny,
                                  patron_type_children_martigny,
                                  patron_martigny_data):
    """Test patron secure api delete."""
    data = deepcopy(patron_martigny_data)
    data['username'] = 'api_delete'
    data['email'] = 'api_delete@test.ch'
    patron = create_patron(data)
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=patron.pid)

    res = client.delete(record_url)
    assert res.status_code == 204

    # try to delete itself
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=librarian_martigny.pid)
    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res = client.delete(record_url)
    assert res.status_code == 403

    # clean up
    ds = app.extensions['invenio-accounts'].datastore
    ds.delete_user(ds.find_user(id=data['user_id']))


def test_patrons_dirty_barcode(
        client, patron_martigny, librarian_martigny):
    """Test patron update with dirty barcode."""
    barcode = patron_martigny.get('patron', {}).get('barcode')
    patron_martigny['patron']['barcode'] = ' {barcode} '.format(
                barcode=barcode
            )
    patron_martigny.update(
        patron_martigny, dbcommit=True, reindex=True)
    patron = Patron.get_record_by_pid(patron_martigny.pid)
    assert patron.patron.get('barcode') == barcode

    # Ensure that users with no patron role will not have a barcode
    librarian_martigny.update(
        librarian_martigny, dbcommit=True, reindex=True)
    assert not librarian_martigny.get('patron', {}).get('barcode')


def test_patrons_circulation_informations(
     client, patron_sion, librarian_martigny,
     patron3_martigny_blocked):
    """test patron circulation informations."""
    url = url_for(
        'api_patrons.patron_circulation_informations',
        patron_pid=patron_sion.pid
    )
    res = client.get(url)
    assert res.status_code == 401

    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert len(data['messages']) == 0

    url = url_for(
        'api_patrons.patron_circulation_informations',
        patron_pid=patron3_martigny_blocked.pid
    )
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert 'error' == data['messages'][0]['type']
    assert 'This patron is currently blocked' in data['messages'][0]['content']

    url = url_for(
        'api_patrons.patron_circulation_informations',
        patron_pid='dummy_pid'
    )
    res = client.get(url)
    assert res.status_code == 404
