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

"""Tests availability."""

from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.documents.views import can_request
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.items.views import item_availability_text
from rero_ils.modules.loans.api import LoanAction
from rero_ils.modules.locations.api import Location
from rero_ils.modules.utils import get_ref_for_pid


def test_item_can_request(
        client, document, holding_lib_martigny, item_lib_martigny,
        librarian_martigny_no_email, lib_martigny,
        patron_martigny_no_email, circulation_policies,
        patron_type_children_martigny, loc_public_martigny_data,
        system_librarian_martigny_no_email, item_lib_martigny_data):
    """Test item can request API."""
    # test no logged user
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 401

    result = can_request(item_lib_martigny)
    assert not result

    login_user_via_session(client, librarian_martigny_no_email.user)
    # valid test
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('can')

    # test no valid -- patron doesn't have correct role
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=system_librarian_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can')

    # test no valid item
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid='no_item',
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 404

    # test no valid library
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid='no_library',
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 404

    # test no valid patron
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode='no_barcode'
        )
    )
    assert res.status_code == 404

    # test no valid item status
    item_lib_martigny['status'] = ItemStatus.MISSING
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can')
    item_lib_martigny['status'] = ItemStatus.ON_SHELF
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)

    # Location :: allow_request == false
    #   create a new location and set 'allow_request' to false. Assign a new
    #   item to this location. Chek if this item can be requested : it couldn't
    #   with 'Item location doesn't allow request' reason.
    new_location = deepcopy(loc_public_martigny_data)
    del new_location['pid']
    new_location['allow_request'] = False
    new_location = Location.create(new_location, dbcommit=True, reindex=True)
    assert new_location
    new_item = deepcopy(item_lib_martigny_data)
    del new_item['pid']
    new_item['barcode'] = 'dummy_barcode_allow_request'
    new_item['location']['$ref'] = get_ref_for_pid(Location, new_location.pid)
    new_item = Item.create(new_item, dbcommit=True, reindex=True)
    assert new_item

    res = client.get(url_for('api_item.can_request', item_pid=new_item.pid))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can')

    # remove created data
    item_url = url_for(
        'invenio_records_rest.item_item',
        pid_value=new_item.pid
    )
    hold_url = url_for(
        'invenio_records_rest.hold_item',
        pid_value=new_item.holding_pid
    )
    loc_url = url_for(
        'invenio_records_rest.loc_item',
        pid_value=new_location.pid
    )
    client.delete(item_url)
    client.delete(hold_url)
    client.delete(loc_url)


def test_item_holding_document_availability(
        client, document, lib_martigny,
        holding_lib_martigny,
        item_lib_martigny, item2_lib_martigny,
        librarian_martigny_no_email, librarian_saxon_no_email,
        patron_martigny_no_email, patron2_martigny_no_email,
        loc_public_saxon, circulation_policies, ebook_1_data,
        item_lib_martigny_data):
    """Test item, holding and document availability."""
    assert item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert item_lib_martigny.available
    assert item_availability_text(item_lib_martigny) == 'on shelf'
    assert holding_lib_martigny.available
    assert holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_martigny_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert document.is_available(view_code='global')
    assert document_availability_status(
        client, document.pid, librarian_martigny_no_email.user)

    # login as patron
    with mock.patch(
        'rero_ils.modules.patrons.api.current_patron',
        patron_martigny_no_email
    ):
        login_user_via_session(client, patron_martigny_no_email.user)
        assert holding_lib_martigny.get_holding_loan_conditions() \
            == 'short 15 days'

    # request
    login_user_via_session(client, librarian_martigny_no_email.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_saxon.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.REQUEST].get('pid')
    assert not item_lib_martigny.available
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert item_availability_text(item_lib_martigny) == '1 request'
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.available
    assert holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_martigny_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert document.is_available('global')
    assert document_availability_status(
        client, document.pid, librarian_martigny_no_email.user)

    # validate request
    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    assert not item_lib_martigny.available
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert not item_lib_martigny.available
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item_availability_text(item) == 'in transit (1 request)'
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.available
    assert holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_martigny_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert document.is_available('global')
    assert document_availability_status(
        client, document.pid, librarian_martigny_no_email.user)
    login_user_via_session(client, librarian_saxon_no_email.user)
    # receive
    res, _ = postdata(
        client,
        'api_item.receive',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    assert not item_lib_martigny.available
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_saxon_no_email.user)
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.available
    assert item_availability_text(item) == '1 request'
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.available
    assert holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_saxon_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert document.is_available('global')
    assert document_availability_status(
        client, document.pid, librarian_martigny_no_email.user)
    # checkout
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.available
    assert not item_availablity_status(
        client, item.pid, librarian_martigny_no_email.user)
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.available
    assert holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_saxon_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert document.is_available('global')
    assert document_availability_status(
        client, document.pid, librarian_martigny_no_email.user)

    # test can not request item already checked out to patron
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can_request')

    class current_i18n:
        class locale:
            language = 'en'
    with mock.patch(
        'rero_ils.modules.items.api.circulation.current_i18n',
        current_i18n
    ):
        end_date = item.get_item_end_date()
        assert item_availability_text(item) == 'due until ' + end_date

    """
    request second item with another patron and test document and holding
    availability
    """

    # login as patron
    with mock.patch(
        'rero_ils.modules.patrons.api.current_patron',
        patron_martigny_no_email
    ):
        login_user_via_session(client, patron2_martigny_no_email.user)
        assert holding_lib_martigny.get_holding_loan_conditions() \
            == 'short 15 days'
    # request second item
    login_user_via_session(client, librarian_martigny_no_email.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            pickup_location_pid=loc_public_saxon.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.REQUEST].get('pid')
    assert not item2_lib_martigny.available
    assert not item_availablity_status(
        client, item2_lib_martigny.pid, librarian_martigny_no_email.user)
    assert item_availability_text(item2_lib_martigny) == '1 request'
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert not holding.available
    assert not holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_martigny_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert not document.is_available('global')
    assert not document_availability_status(
        client, document.pid, librarian_martigny_no_email.user)


def item_availablity_status(client, pid, user):
    """Returns item availability."""
    login_user_via_session(client, user)
    res = client.get(
        url_for(
            'api_item.item_availability',
            item_pid=pid,
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get('availability')


def holding_availablity_status(client, pid, user):
    """Returns holding availability."""
    login_user_via_session(client, user)
    res = client.get(
        url_for(
            'api_holding.holding_availability',
            holding_pid=pid,
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get('availability')


def document_availability_status(client, pid, user):
    """Returns document availability."""
    login_user_via_session(client, user)
    res = client.get(
        url_for(
            'api_documents.document_availability',
            document_pid=pid,
            view_code='global'
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get('availability')


def test_availability_cipo_allow_request(
        client, librarian_martigny_no_email, item_lib_martigny,
        item_type_standard_martigny, patron_martigny_no_email,
        circ_policy_short_martigny):
    """Test availability is cipo disallow request."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    # update the cipo to disallow request
    cipo = circ_policy_short_martigny
    cipo['allow_requests'] = False
    cipo.update(cipo.dumps(), dbcommit=True, reindex=True)

    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            patron_barcode=patron_martigny_no_email.get('barcode')
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can')

    # reset the cipo
    cipo['allow_requests'] = True
    cipo.update(cipo.dumps(), dbcommit=True, reindex=True)


def test_document_availability_failed(client, librarian2_martigny_no_email):
    """Test document availability with dummy data should failed."""
    login_user_via_session(client, librarian2_martigny_no_email.user)
    res = client.get(
        url_for(
            'api_documents.document_availability',
            document_pid='dummy_pid'
        )
    )
    assert res.status_code == 404


def test_item_availability_failed(client, librarian2_martigny_no_email):
    """Test item availability with dummy data should failed."""
    login_user_via_session(client, librarian2_martigny_no_email.user)
    res = client.get(
        url_for(
            'api_item.item_availability',
            item_pid='dummy_pid'
        )
    )
    assert res.status_code == 404
