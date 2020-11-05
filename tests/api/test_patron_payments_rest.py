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

"""Tests REST API patron payments."""

from copy import deepcopy

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.utils import get_ref_for_pid


def test_patron_payment(
        client, librarian_martigny_no_email,
        librarian_sion_no_email, patron_transaction_overdue_event_martigny):
    """Test patron payment."""
    transaction = \
        patron_transaction_overdue_event_martigny.patron_transaction()
    calculated_amount = sum([event.amount
                             for event in
                             transaction.events])
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert calculated_amount == transaction.total_amount == 2.00

    login_user_via_session(client, librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.ptre_list'
    payment = deepcopy(patron_transaction_overdue_event_martigny)

    # partial payment
    del payment['pid']
    payment['type'] = 'payment'
    payment['subtype'] = 'cash'
    payment['amount'] = 0.54
    payment['operator'] = {'$ref': get_ref_for_pid(
        'patrons', librarian_martigny_no_email.pid)}
    res, _ = postdata(
        client,
        post_entrypoint,
        payment
    )
    assert res.status_code == 201
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert transaction.total_amount == 1.46
    assert transaction.status == 'open'

    # full payment
    payment['type'] = 'payment'
    payment['subtype'] = 'cash'
    payment['amount'] = 1.46
    res, _ = postdata(
        client,
        post_entrypoint,
        payment
    )
    assert res.status_code == 201

    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert transaction.total_amount == 0.00
    assert transaction.status == 'closed'
