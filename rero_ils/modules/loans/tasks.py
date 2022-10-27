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

from ..items.api import Item
from ..loans.api import Loan, LoansSearch, get_expired_request
from ..utils import set_timestamp


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
            loan.anonymize(loan, dbcommit=dbcommit, reindex=reindex)
            counter += 1

    set_timestamp('anonymize-loans', count=counter)
    return counter


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
