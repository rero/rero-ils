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
from copy import deepcopy

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.errors import InvalidRecordID
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import LoanAction


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


def test_checkout_no_loan_given(client, librarian_martigny_no_email,
                                patron_martigny_no_email, loc_public_martigny,
                                item_lib_martigny, json_header,
                                circulation_policies):
    """Test checkout item when request loan is not given."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron = patron_martigny_no_email
    location = loc_public_martigny
    # request
    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item.pid,
            pickup_location_pid=location.pid,
            patron_pid=patron.pid
        )
    )
    assert res.status_code == 200

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid,
            patron_pid=patron.pid
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')

    from rero_ils.modules.patrons.views import \
        get_patron_from_checkout_item_pid
    assert get_patron_from_checkout_item_pid(item.pid) == patron

    res, _ = postdata(client, 'api_item.checkin', dict(item_pid=item.pid))
    assert res.status_code == 403

    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            pid=loan_pid
        ),
    )
    assert res.status_code == 200


def test_item_misc(client, librarian_martigny_no_email, lib_martigny,
                   patron_martigny_no_email, loc_public_martigny,
                   item_lib_martigny, json_header, item_type_standard_martigny,
                   circ_policy_short_martigny, patron_type_children_martigny):
    """Test item different functions."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron = patron_martigny_no_email
    location = loc_public_martigny
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    assert not item.get_extension_count()
    assert not item.get_loan_pid_with_item_in_transit(item.pid)
    assert not item.get_loan_pid_with_item_on_loan(item.pid)
    assert not item.get_item_by_barcode(barcode='does not exist')

    loans = item.get_checked_out_loans('does not exist')

    with pytest.raises(InvalidRecordID):
        assert sum(1 for loan in loans)

    assert 'checkout' in item.actions

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item.pid,
            pickup_location_pid=location.pid,
            patron_pid=patron.pid
        ),
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('pid')

    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item.pid,
            pid=loan_pid
        ),
    )
    assert res.status_code == 200

    circ_policy['allow_checkout'] = False
    circ_policy['renewal_duration'] = 30

    circ_policy.update(circ_policy, dbcommit=True, reindex=True)
    assert not circ_policy.get('allow_checkout')
    assert 'checkout' not in item.actions

    circ_policy['allow_checkout'] = True
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )

    # checkout
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid,
            patron_pid=patron.pid,
            pid=loan_pid
        ),
    )
    assert res.status_code == 200
    assert 'extend_loan' in item.actions

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.items.api.circulation.current_i18n',
        current_i18n
    ):
        assert item.get_item_end_date()

    circ_policy.update(circ_policy_origin, dbcommit=True, reindex=True)
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            pid=loan_pid
        ),
    )
    assert res.status_code == 200

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.items.api.circulation.current_i18n',
        current_i18n
    ):
        assert not item.get_item_end_date()


def test_automatic_checkin(client, librarian_martigny_no_email, lib_martigny,
                           patron_martigny_no_email, loc_public_martigny,
                           item_lib_martigny, json_header,
                           item_type_standard_martigny,
                           circ_policy_short_martigny,
                           patron_type_children_martigny, lib_saxon,
                           loc_public_saxon, librarian_saxon_no_email):
    """Test item automatic checkin."""
    login_user_via_session(client, librarian_saxon_no_email.user)
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    record, actions = item_lib_martigny.automatic_checkin()
    assert actions == {'no': None}

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron_martigny_no_email.pid
        ),
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('pid')

    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item.status == ItemStatus.IN_TRANSIT

    record, actions = item.automatic_checkin()
    assert 'receive' in actions

    item.cancel_loan(pid=loan_pid)
    assert item.status == ItemStatus.ON_SHELF


def test_item_different_actions(client, librarian_martigny_no_email,
                                lib_martigny,
                                patron_martigny_no_email, loc_public_martigny,
                                item_lib_martigny, json_header,
                                item_type_standard_martigny,
                                circ_policy_short_martigny,
                                patron_type_children_martigny, lib_saxon,
                                loc_public_saxon, librarian_saxon_no_email):
    """Test item possible actions other scenarios."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    patron_pid = patron_martigny_no_email.pid
    res = client.get(
        url_for(
            'api_item.item',
            item_barcode='does not exist',
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 404

    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')

    record = Item.get_record_by_pid(item_lib_martigny.pid)

    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid='does not exist',
            pid=loan_pid,
            transaction_location_pid=loc_public_saxon.pid
        ),
    )
    assert res.status_code == 404

    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_saxon.pid
        ),
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKIN].get('pid')

    data = {'pid': loan_pid}
    params, actions = item_lib_martigny.prior_checkout_actions(data)
    assert 'cancel' in actions


def test_item_secure_api(client, json_header, item_lib_martigny,
                         librarian_martigny_no_email, librarian_sion_no_email):
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
            pickup_location_pid=loc_public_martigny.pid
        )
    )

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid
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
                                item2_lib_martigny,
                                circulation_policies):
    """Test sort of checkout loans."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
        ),
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
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
    assert items[1]['item']['pid'] == item2_lib_martigny.pid

    # sort by transaction_date desc
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny_no_email.pid,
            sort='-transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    items = data['hits']['hits']

    assert items[0]['item']['pid'] == item2_lib_martigny.pid
    assert items[1]['item']['pid'] == item3_lib_martigny.pid

    # sort by invalid field
    res = client.get(
        url_for(
            'api_item.loans', patron_pid=patron_martigny_no_email.pid,
            sort='does not exist'))
    assert res.status_code == 500
    data = get_json(res)
    assert 'RequestError(400' in data['status']


def test_checkout_cancel_old_loan(
        client, librarian_martigny_no_email, patron_martigny_no_email,
        loc_public_martigny, item_lib_fully, circulation_policies,
        patron2_martigny_no_email):
    """Test prior checkin actions."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    # request an item by a librarian in a remote location
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_fully.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('pid')
    # validate the request to loan status goes to in_transit
    item_lib_fully.validate_request(pid=loan_pid)
    action_params = {'patron_pid': patron2_martigny_no_email.pid}
    # loan will be canclled if a librarian decided to checkout the item anyway.
    item, actions = item_lib_fully.prior_checkout_actions(action_params)
    assert 'cancel' in actions
