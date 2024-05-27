# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""Test item/loan circulation auto extend task."""
from datetime import datetime, timedelta, timezone

from rero_ils.modules.items.models import ItemCirculationAction, ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.tasks import automatic_renewal
from rero_ils.modules.loans.utils import get_circ_policy
from rero_ils.modules.operation_logs.api import OperationLogsSearch


def test_auto_extend_task(item_on_loan_martigny_patron_and_loan_on_loan,
                          loc_public_martigny, patron2_martigny,
                          librarian_martigny, mailbox):
    """Test the automatic extension of on_loan item."""
    # Prepare a loan where the due date is today
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    cipo = get_circ_policy(loan)
    start_date = datetime.now(timezone.utc) - timedelta(
        days=cipo['checkout_duration'])
    end_date = datetime.now(timezone.utc)
    loan['start_date'] = start_date.isoformat()
    loan['end_date'] = end_date.isoformat()
    loan['transaction_date'] = start_date.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    loan = loan.get_record_by_pid(loan.pid)

    # If automatic_renewal is not set in the policy, the loan is
    # not renewed.
    cipo.pop('automatic_renewal', None)
    cipo.update(cipo, dbcommit=True, reindex=True)

    result = automatic_renewal()
    loan = Loan.get_record_by_pid(loan.pid)

    # Check that no loan was extended and no loan was ignored
    # (because the unextended loan was filtered directly in the first query)
    assert result == (0, 0)
    assert item.status == ItemStatus.ON_LOAN
    assert not loan.get('auto_extend')
    assert not mailbox

    # If loan is not renewable (request exists), it is ignored
    cipo['automatic_renewal'] = True
    cipo.update(cipo, dbcommit=True, reindex=True)

    # Add a request to the same item
    item, actions = item.request(
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    requested_loan_pid = actions['request']['pid']

    result = automatic_renewal()
    extended_loan = Loan.get_record_by_pid(loan.pid)

    # Check that no loan was extended
    # and one loan was ignored because not renewable
    assert result == (0, 1)
    assert item.status == ItemStatus.ON_LOAN
    assert not extended_loan.get('auto_extend')
    assert not mailbox

    # Cancel the request made for the previous test
    item.cancel_item_request(pid=requested_loan_pid,
                             transaction_location_pid=loc_public_martigny.pid,
                             transaction_user_pid=librarian_martigny.pid)

    # If patron is blocked, the loan extend is ignored
    cipo['automatic_renewal'] = True
    cipo.update(cipo, dbcommit=True, reindex=True)

    patron['patron']['blocked'] = True
    patron.update(patron, dbcommit=True, reindex=True)

    result = automatic_renewal()
    extended_loan = Loan.get_record_by_pid(loan.pid)

    # Check that no loan was extended
    # and one loan was ignored because not renewable (patron blocked)
    assert result == (0, 1)
    assert item.status == ItemStatus.ON_LOAN
    assert not extended_loan.get('auto_extend')
    assert not mailbox

    # unblock patron
    patron['patron'].pop('blocked')
    patron.update(patron, dbcommit=True, reindex=True)

    # If renewals number is not allowed in cipo, the extend is ignored
    cipo['number_renewals'] = 0
    cipo.update(cipo, dbcommit=True, reindex=True)

    result = automatic_renewal()
    extended_loan = Loan.get_record_by_pid(loan.pid)

    # Check that no loan was extended
    # and one loan was ignored because the cipo disallows the extend
    assert result == (0, 1)
    assert item.status == ItemStatus.ON_LOAN
    assert not extended_loan.get('auto_extend')
    assert not mailbox

    # reset cipo
    cipo['number_renewals'] = 3
    cipo.update(cipo, dbcommit=True, reindex=True)

    # Auto extend one extendable loan
    result = automatic_renewal()
    assert result == (1, 0)
    assert item.status == ItemStatus.ON_LOAN
    extended_loan = Loan.get_record_by_pid(loan.pid)
    assert extended_loan.get('auto_extend') is True

    # Check that the notification was correctly sent
    assert len(mailbox) == 1
    assert mailbox[0].recipients == [
        'reroilstest+martigny+auto_extend@gmail.com']

    # Check that the operation_logs were created
    OperationLogsSearch.flush_and_refresh()
    es_query = OperationLogsSearch()\
        .filter('term', loan__pid=loan.pid)\
        .filter('term', record__type='loan')\
        .filter('term', loan__trigger=ItemCirculationAction.EXTEND)\
        .filter('term', loan__auto_extend=True)
    assert es_query.count() == 1

    es_query = OperationLogsSearch()\
        .filter('term', loan__pid=loan.pid)\
        .filter('term', record__type='notif')\
        .filter('term', loan__trigger=ItemCirculationAction.EXTEND)\
        .filter('term', notification__type='auto_extend')
    assert es_query.count() == 1
