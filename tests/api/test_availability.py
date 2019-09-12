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

import mock
import pytz
from dateutil import parser
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.filter import format_date_filter
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.views import item_availability_text
from rero_ils.modules.loans.api import LoanAction


def test_item_holding_document_availability(
        client, document,
        holding_lib_martigny,
        item_lib_martigny, item2_lib_martigny,
        librarian_martigny_no_email, librarian_saxon_no_email,
        patron_martigny_no_email, patron2_martigny_no_email,
        loc_public_saxon, circulation_policies):
    """Test item, holding and document availability."""
    assert item_availablity_status(
        client, item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert item_lib_martigny.available
    assert item_availability_text(item_lib_martigny) == 'on_shelf'
    assert holding_lib_martigny.available
    assert holding_availablity_status(
        client, holding_lib_martigny.pid, librarian_martigny_no_email.user)
    assert holding_lib_martigny.get_holding_loan_conditions() == 'standard'
    assert document.is_available(view_code='global')
    assert document_availablity_status(
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
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron_martigny_no_email.pid
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
    assert document_availablity_status(
        client, document.pid, librarian_martigny_no_email.user)
    # validate request
    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid
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
    assert document_availablity_status(
        client, document.pid, librarian_martigny_no_email.user)
    login_user_via_session(client, librarian_saxon_no_email.user)
    # receive
    res, _ = postdata(
        client,
        'api_item.receive',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid
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
    assert document_availablity_status(
        client, document.pid, librarian_martigny_no_email.user)
    # checkout
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
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
    assert document_availablity_status(
        client, document.pid, librarian_martigny_no_email.user)

    class current_i18n:
        class locale:
            language = 'en'
    with mock.patch(
        'rero_ils.modules.items.api.current_i18n',
        current_i18n
    ):
        end_date = pytz.utc.localize(parser.parse(item.get_item_end_date()))
        end_date = format_date_filter(end_date, format='short_date')
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
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron2_martigny_no_email.pid
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
    assert not document_availablity_status(
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


def document_availablity_status(client, pid, user):
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
