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

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.views import can_request
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.models import LoanAction
from rero_ils.modules.locations.api import Location
from rero_ils.modules.utils import get_ref_for_pid


def test_item_can_request(
    client, document, holding_lib_martigny, item_lib_martigny,
    librarian_martigny, lib_martigny, loc_public_martigny,
    patron_martigny, circulation_policies,
    patron_type_children_martigny, loc_public_martigny_data,
    system_librarian_martigny, item_lib_martigny_data,
    yesterday, tomorrow
):
    """Test item can request API."""
    # test no logged user
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
        )
    )
    assert res.status_code == 401

    can, _ = can_request(item_lib_martigny)
    assert not can

    login_user_via_session(client, librarian_martigny.user)
    # valid test
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('can')

    # test no valid item
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid='no_item',
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
        )
    )
    assert res.status_code == 404

    # test no valid library
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid='no_library',
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
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
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can')
    item_lib_martigny['status'] = ItemStatus.ON_SHELF
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)

    # Location :: allow_request == false
    #   create a new location and set 'allow_request' to false. Assign a new
    #   item to this location. Check if the item can be requested : it couldn't
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
    assert not res.json.get('can')

    # Same test with temporary_location disallowing request.
    #   * Main location of the new item allow request
    #   --> the request is allowed
    #   * Temporary location of the new item disallow request
    #   --> the request is disallowed
    #   * with an obsolete temporary location
    #   --> the request is allowed
    new_item['location']['$ref'] = get_ref_for_pid(
        Location, loc_public_martigny.pid)
    assert loc_public_martigny.get('allow_request')
    new_item.update(new_item, dbcommit=True, reindex=True)
    res = client.get(url_for('api_item.can_request', item_pid=new_item.pid))
    assert res.status_code == 200
    assert res.json.get('can')

    new_item['temporary_location'] = {
        '$ref': get_ref_for_pid(Location, new_location.pid),
        'end_date': tomorrow.strftime('%Y-%m-%d')
    }
    new_item.update(new_item, dbcommit=True, reindex=True)
    res = client.get(url_for('api_item.can_request', item_pid=new_item.pid))
    assert res.status_code == 200
    assert not res.json.get('can')

    new_item['temporary_location']['end_date'] = yesterday.strftime('%Y-%m-%d')
    new_item.update(new_item, dbcommit=True, reindex=True)
    res = client.get(url_for('api_item.can_request', item_pid=new_item.pid))
    assert res.status_code == 200
    assert res.json.get('can')

    # remove created data
    client.delete(url_for(
        'invenio_records_rest.item_item',
        pid_value=new_item.pid
    ))
    client.delete(url_for(
        'invenio_records_rest.hold_item',
        pid_value=new_item.holding_pid
    ))
    client.delete(url_for(
        'invenio_records_rest.loc_item',
        pid_value=new_location.pid
    ))


def test_item_holding_document_availability(
        client, document, lib_martigny,
        holding_lib_martigny,
        item_lib_martigny, item2_lib_martigny,
        librarian_martigny, librarian_saxon,
        patron_martigny, patron2_martigny,
        loc_public_saxon, circulation_policies, ebook_1_data,
        item_lib_martigny_data):
    """Test item, holding and document availability."""
    assert item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny.user)
    assert item_lib_martigny.is_available()
    assert holding_lib_martigny.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert Document.is_available(document.pid, view_code='global')
    assert document_availability_status(
        client, document.pid, librarian_martigny.user)

    # login as patron
    with mock.patch(
        'rero_ils.modules.patrons.api.current_patrons',
        [patron_martigny]
    ):
        login_user_via_session(client, patron_martigny.user)
        assert holding_lib_martigny.get_holding_loan_conditions() \
            == 'short 15 days'

    # request
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.REQUEST].get('pid')
    assert not item_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny.user)
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert Document.is_available(document.pid, 'global')
    assert document_availability_status(
        client, document.pid, librarian_martigny.user)

    # validate request
    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    assert not item_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny.user)
    assert not item_lib_martigny.is_available()
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert Document.is_available(document.pid, 'global')
    assert document_availability_status(
        client, document.pid, librarian_martigny.user)
    login_user_via_session(client, librarian_saxon.user)
    # receive
    res, _ = postdata(
        client,
        'api_item.receive',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    assert not item_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item_lib_martigny.pid, librarian_saxon.user)
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.is_available()
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert Document.is_available(document.pid, 'global')
    assert document_availability_status(
        client, document.pid, librarian_martigny.user)
    # checkout
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.is_available()
    assert not item_availablity_status(
        client, item.pid, librarian_martigny.user)
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert Document.is_available(document.pid, 'global')
    assert document_availability_status(
        client, document.pid, librarian_martigny.user)

    # masked item isn't.is_available()
    item['_masked'] = True
    item = item.update(item, dbcommit=True, reindex=True)
    assert not item.is_available()
    del item['_masked']
    item.update(item, dbcommit=True, reindex=True)

    # test can not request item already checked out to patron
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can_request')

    end_date = item.get_item_end_date(time_format=None,
                                      language='en')

    """
    request second item with another patron and test document and holding
    availability
    """

    # login as patron
    with mock.patch(
        'rero_ils.modules.patrons.api.current_patrons',
        [patron_martigny]
    ):
        login_user_via_session(client, patron2_martigny.user)
        assert holding_lib_martigny.get_holding_loan_conditions() \
            == 'short 15 days'
    # request second item
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron2_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    assert not item2_lib_martigny.is_available()
    assert not item_availablity_status(
        client, item2_lib_martigny.pid, librarian_martigny.user)
    holding = Holding.get_record_by_pid(holding_lib_martigny.pid)
    assert not holding.is_available()
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert not Document.is_available(document.pid, 'global')
    assert not document_availability_status(
        client, document.pid, librarian_martigny.user)


def item_availablity_status(client, pid, user):
    """Returns item availability."""
    res = client.get(
        url_for(
            'api_item.item_availability',
            pid=pid,
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get('available')


def document_availability_status(client, pid, user):
    """Returns document availability."""
    res = client.get(
        url_for(
            'api_documents.document_availability',
            pid=pid,
            view_code='global'
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    return data.get('available')


def test_availability_cipo_allow_request(
        client, librarian_martigny, item_lib_martigny,
        item_type_standard_martigny, patron_martigny,
        circ_policy_short_martigny):
    """Test availability is cipo disallow request."""
    login_user_via_session(client, librarian_martigny.user)

    # update the cipo to disallow request
    cipo = circ_policy_short_martigny
    cipo['allow_requests'] = False
    cipo.update(cipo.dumps(), dbcommit=True, reindex=True)

    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_lib_martigny.pid,
            patron_barcode=patron_martigny.get(
                'patron', {}).get('barcode')[0]
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can')

    # reset the cipo
    cipo['allow_requests'] = True
    cipo.update(cipo.dumps(), dbcommit=True, reindex=True)


def test_document_availability_failed(
        client, item_lib_martigny, document_with_issn, org_martigny):
    """Test document availability with dummy data should failed."""
    res = client.get(
        url_for(
            'api_documents.document_availability',
            pid='dummy_pid'
        )
    )
    assert res.status_code == 404
    res = client.get(
        url_for(
            'api_documents.document_availability',
            pid=document_with_issn.pid
        )
    )
    assert res.status_code == 200
    assert not res.json.get('available')
    res = client.get(
        url_for(
            'api_documents.document_availability',
            pid=document_with_issn.pid,
            view_code=org_martigny['code']
        )
    )
    assert res.status_code == 200
    assert not res.json.get('available')


def test_item_availability_failed(client, librarian2_martigny):
    """Test item availability with dummy data should failed."""
    res = client.get(
        url_for(
            'api_item.item_availability',
            pid='dummy_pid'
        )
    )
    assert res.status_code == 404


def test_item_availability_extra(client, item_lib_sion):
    """Test item availability with an extra parameters."""
    res = client.get(
        url_for(
            'api_item.item_availability',
            pid=item_lib_sion.pid
        )
    )
    assert list(res.json.keys()) == ['available']

    res = client.get(
        url_for(
            'api_item.item_availability',
            pid=item_lib_sion.pid,
            more_info=1
        )
    )
    assert list(res.json.keys()) == \
        ['available', 'circulation_message', 'number_of_request', 'status']


def test_holding_availability(client, holding_lib_martigny):
    """Test holding availability endpoint."""
    res = client.get(
        url_for(
            'api_holding.holding_availability',
            pid='dummy_pid'
        )
    )
    assert res.status_code == 404

    res = client.get(
        url_for(
            'api_holding.holding_availability',
            pid=holding_lib_martigny.pid
        )
    )
    assert res.status_code == 200
    assert 'available' in res.json
