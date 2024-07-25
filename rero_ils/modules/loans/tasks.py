# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Celery tasks for loan records."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta, timezone

import click
from celery import shared_task

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.tasks import process_notifications
from rero_ils.modules.utils import set_timestamp

from .api import Loan, LoansSearch, get_expired_request, get_overdue_loans
from .utils import get_circ_policy


@shared_task(ignore_result=True)
def loan_anonymizer(dbcommit=True, reindex=True):
    """Job to anonymize loans for all organisations.

    :param reindex: reindex the records.
    :param dbcommit: commit record to database.
    :return a count of updated loans.
    """
    counter = 0
    for loan in Loan.get_anonymized_candidates():
        if Loan.can_anonymize(loan_data=loan, patron=None):
            loan.anonymize(dbcommit=dbcommit, reindex=reindex)
            counter += 1

    set_timestamp('anonymize-loans', count=counter)
    return counter


@shared_task(ignore_result=True)
def automatic_renewal(tstamp=None):
    """Extend all loans with an automatic renewal policy.

    :param tstamp: the timestamp to check. Default is `datetime.now()`
    :returns: a tuple containing the number of loans that have been extended
              and the number of loans where the circulation action was not
              possible.
    """
    extended_loans_count = 0
    ignored_loans_count = 0
    tstamp = tstamp or datetime.now(timezone.utc)
    # get all loans that are due today or earlier (will be overdue tomorrow)
    until_date = tstamp + timedelta(days=1)
    for loan in get_overdue_loans(tstamp=until_date):
        policy = get_circ_policy(loan)
        if policy.get('automatic_renewal'):
            if item := Item.get_record_by_pid(loan.item_pid):
                if item.can(
                    action=ItemCirculationAction.EXTEND,
                    patron_pid=loan.patron_pid,
                    loan=loan
                )[0]:
                    item.extend_loan(
                        pid=loan.pid,
                        transaction_location_pid=loan.location_pid,
                        transaction_user_pid=loan.patron_pid,
                        auto_extend=True
                    )
                    extended_loans_count += 1
                else:
                    ignored_loans_count += 1
    process_notifications(NotificationType.AUTO_EXTEND)
    return extended_loans_count, ignored_loans_count


@shared_task(ignore_result=True)
def cancel_expired_request_task(tstamp=None):
    """Cancel all expired loans for all organisations.

    :param tstamp: the timestamp to check. Default is `datetime.now()`
    :return a tuple with total performed loans ans total cancelled loans.
    """
    total_loans_counter = total_cancelled_loans = 0
    for loan in get_expired_request(tstamp):
        total_loans_counter += 1
        item = Item.get_record_by_pid(loan.item_pid)
        # TODO : trans_user_pid shouldn't be the patron itself, but a system
        #        user.
        _, actions = item.cancel_item_request(
            loan.pid,
            transaction_location_pid=loan.location_pid,
            transaction_user_pid=loan.patron_pid
        )
        if actions.get('cancel', {}).get('pid') == loan.pid:
            total_cancelled_loans += 1
    set_timestamp('cancel-expired-request-task', total=total_loans_counter,
                  cancelled=total_cancelled_loans)
    return total_loans_counter, total_cancelled_loans


@shared_task(ignore_result=True)
def delete_loans_created(verbose=False, hours=1, dbcommit=True, delindex=True):
    """Delete loans with state CREATED from time NOW - hours."""
    now = datetime.now(timezone.utc)
    if hours >= 0:
        now -= timedelta(hours=hours)
    count = LoansSearch().filter('term', state='CREATED').count()
    query = LoansSearch() \
        .filter('term', state='CREATED').filter('range', _created={'lt': now})
    if verbose:
        click.echo(
            f'TOTAL: {count} DELETE: {query.count()} HOURS: {-query.count()}'
        )
    idx = 0
    for idx, hit in enumerate(query.source('pid').scan(), 1):
        loan = Loan.get_record_by_pid(hit.pid)
        state = loan.get('state')
        if verbose:
            click.echo(f'{idx:<10} {loan.pid:<10} {state} DELETE')
        loan.delete(dbcommit=dbcommit, delindex=delindex)
    return idx
