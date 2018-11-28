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

from datetime import datetime, timezone

from invenio_circulation.api import get_loan_for_item

from rero_ils.modules.items.api import ItemStatus
from rero_ils.modules.loans.api import get_pending_loan_by_patron_and_item
from rero_ils.modules.loans.api import \
    get_request_by_item_pid_by_patron_pid as get_request_item_patron

current_date = datetime.now(timezone.utc).isoformat()


def test_request_rankings(
    app, all_resources_limited, all_resources_limited_2, es_clear
):
    """Item rankings."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    (
        doc2,
        item2,
        organisation2,
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
    assert loan_1['patron_pid'] == simonetta.pid
    assert item.patron_request_rank(simonetta.get('barcode')) == 1
    assert item.dumps().get('pending_loans')[0] == loan_1.pid

    new_current_date = datetime.now(timezone.utc).isoformat()
    loan_2 = item.request_item(
        patron_pid=philippe.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=philippe.pid,
        transaction_date=new_current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 2
    assert loan_2['patron_pid'] == philippe.pid
    assert loan_1.pid != loan_2.pid
    assert item.patron_request_rank(philippe.get('barcode')) == 2
    assert item.dumps().get('pending_loans')[1] == loan_2.pid
    loan = item.cancel_item_loan(
        loan_pid=loan_1.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1
    assert loan.pid == loan_1.pid
    assert item.patron_request_rank(philippe.get('barcode')) == 1
    assert item.dumps().get('pending_loans')[0] == loan_2.pid

    new_current_date = datetime.now(timezone.utc).isoformat()

    loan_4 = item.request_item(
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=new_current_date,
        document_pid=doc.pid,
    )
    assert item.number_of_item_requests() == 2
    assert item.patron_request_rank(philippe.get('barcode')) == 1
    assert item.patron_request_rank(simonetta.get('barcode')) == 2
    assert item.dumps().get('pending_loans')[1] == loan_4.pid


def test_multiple_requests(
    app, all_resources_limited, all_resources_limited_2, es_clear
):
    """Item multiple requests."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    (
        doc2,
        item2,
        organisation2,
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
    assert loan_1['patron_pid'] == simonetta.pid

    loan_2 = item.request_item(
        patron_pid=philippe.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=philippe.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 2
    assert loan_2['patron_pid'] == philippe.pid
    assert loan_1.pid != loan_2.pid
    loan = item.cancel_item_loan(
        loan_pid=loan_1.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1
    assert loan.pid == loan_1.pid


def test_checkin_transit_house_receive(
    app, all_resources_limited, all_resources_limited_2, es_clear
):
    """Item checkin, in_tranist, in_house receive testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    (
        doc2,
        item2,
        organisation2,
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
    assert item.number_of_item_requests() == 1
    loan = item.receive_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        pickup_location_pid=location2.pid,
        transaction_location_pid=location2.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.AT_DESK
    assert item.number_of_item_requests() == 1
    loan = item.loan_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location2.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert item.number_of_item_requests() == 0
    loan = item.extend_loan(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location2.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['extension_count'] == 1
    assert item.number_of_item_requests() == 0
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
    loan = item.receive_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0


def test_request_in_transit_checkout_extend_checkin(
    app, all_resources_limited, es_clear, all_resources_limited_2
):
    """Item request, validate, checkout, extend, checkin testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    (
        doc2,
        item2,
        organisation2,
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
    loan_request = get_request_item_patron(item.pid, simonetta.pid)
    loan_request_pid = loan_request['loan_pid']
    assert loan_request_pid == loan.pid
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
    assert item.number_of_item_requests() == 1
    loan = item.receive_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        pickup_location_pid=location2.pid,
        transaction_location_pid=location2.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.AT_DESK
    assert item.number_of_item_requests() == 1
    loan = item.loan_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location2.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['patron_pid'] == simonetta.pid
    loan = item.extend_loan(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location2.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['extension_count'] == 1
    loan = item.return_item(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert not get_loan_for_item(item.pid)


def test_request_validate_checkout_extend_checkin(
    app, all_resources_limited, es_clear
):
    """Item request, validate, checkout, extend, checkin testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
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

    loan = item.validate_item_request(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.AT_DESK
    assert item.number_of_item_requests() == 1

    loan = item.loan_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert get_loan_for_item(item.pid)
    assert loan['patron_pid'] == simonetta.pid
    loan = item.extend_loan(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['extension_count'] == 1
    loan = item.return_item(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert not get_loan_for_item(item.pid)


def test_checkout_extend_checkin(app, all_resources_limited, es_clear):
    """Item checkout, extend, checkin testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    assert not get_loan_for_item(item.pid)
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
    loan = item.extend_loan(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['extension_count'] == 1
    loan = item.return_item(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert not get_loan_for_item(item.pid)


def test_request_checkout_extend_checkin(app, all_resources_limited, es_clear):
    """Item request, checkout, extend, checkin testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert not get_loan_for_item(item.pid)
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
    loan = item.extend_loan(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert get_loan_for_item(item.pid)
    assert loan['extension_count'] == 1
    loan = item.return_item(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert not get_loan_for_item(item.pid)


def test_cancel_item_loan(app, all_resources_limited, es_clear):
    """Cancel item loan testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
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

    loan_req = get_pending_loan_by_patron_and_item(simonetta.pid, item.pid)
    loan_req_pid = loan_req['loan_pid']
    assert loan.pid == loan_req_pid
    assert loan['patron_pid'] == simonetta.pid
    loan = item.cancel_item_loan(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0


def test_validate_item(
    app, all_resources_limited, all_resources_limited_2, es_clear
):
    """Validate item testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    (
        doc2,
        item2,
        organisation2,
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
    assert item.number_of_item_requests() == 1


def test_receive_item(
    app, all_resources_limited, all_resources_limited_2, es_clear
):
    """Receive item testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    (
        doc2,
        item2,
        organisation2,
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
    assert item.number_of_item_requests() == 1
    loan = item.receive_item(
        loan_pid=loan.pid,
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.AT_DESK
    assert item.number_of_item_requests() == 1


def test_request_item(app, all_resources_limited, es_clear):
    """Item request testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    loan_req_1 = item.request_item(
        patron_pid=simonetta.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert loan_req_1.pid
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 1
    loan_req_2 = item.request_item(
        patron_pid=philippe.pid,
        pickup_location_pid=location.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date='2018-02-03',
        document_pid=doc.pid,
    )
    assert loan_req_2.pid
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 2


def test_loan_item(app, all_resources_limited, es_clear):
    """Item checkout testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    assert not get_loan_for_item(item.pid)
    loan = item.loan_item(
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['patron_pid'] == simonetta.pid


def test_return_item(app, all_resources_limited, es_clear):
    """Item checkin testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    assert not get_loan_for_item(item.pid)
    loan = item.loan_item(
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert get_loan_for_item(item.pid)
    loan = item.return_item(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_SHELF
    assert not get_loan_for_item(item.pid)


def test_extend_item(app, all_resources_limited, es_clear):
    """Item renewal testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    assert not get_loan_for_item(item.pid)
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
    loan = item.extend_loan(
        patron_pid=simonetta.pid,
        loan_pid=loan.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert get_loan_for_item(item.pid)
    assert loan['extension_count'] == 1


def test_pending_to_onloan_item(app, all_resources_limited, es_clear):
    """Item checkout after a request testing."""
    (
        doc,
        item,
        organisation,
        library,
        location,
        simonetta,
        philippe,
    ) = all_resources_limited
    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_item_requests() == 0
    assert not get_loan_for_item(item.pid)
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

    loan = item.loan_item(
        patron_pid=simonetta.pid,
        transaction_location_pid=location.pid,
        transaction_user_pid=simonetta.pid,
        transaction_date=current_date,
        document_pid=doc.pid,
    )
    assert item.status == ItemStatus.ON_LOAN
    assert loan['patron_pid'] == simonetta.pid
