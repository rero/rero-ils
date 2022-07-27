# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Utility functions about PatronTransactions."""
from datetime import datetime, timezone

from flask_babelex import gettext as _

from .api import PatronTransaction, PatronTransactionsSearch
from ..utils import get_ref_for_pid


def _build_transaction_query(patron_pid, status=None, types=None):
    """Private function to build a transaction query linked to a patron.

    :param patron_pid: the patron pid being searched
    :param status: (optional) array of transaction status filter,
    :param types: (optional) array of transaction types filter,
    :return: return prepared query.
    """
    query = PatronTransactionsSearch() \
        .filter('term', patron__pid=patron_pid)
    if status:
        query = query.filter('term', status=status)
    if types:
        query = query.filter('terms', type=types)
    return query


def get_transactions_pids_for_patron(patron_pid, status=None):
    """Get patron transactions linked to a patron.

    :param patron_pid: the patron pid being searched
    :param status: (optional) transaction status filter,
    """
    query = _build_transaction_query(patron_pid, status)
    for result in query.source('pid').scan():
        yield result.pid


def get_transactions_count_for_patron(patron_pid, status=None):
    """Get patron transactions count linked to a patron.

    :param patron_pid: the patron pid being searched
    :param status: (optional) transaction status filter,
    """
    query = _build_transaction_query(patron_pid, status)
    return query.source().count()


def get_transactions_total_amount_for_patron(
     patron_pid, status=None, types=None, with_subscription=True):
    """Get total amount transactions linked to a patron.

    :param patron_pid: the patron pid being searched
    :param status: (optional) transaction status filter,
    :param types: (optional) transaction type filter,
    :param with_subscription: (optional) include or exclude subscription
           type filter.
    :return: return total amount of transactions.
    """
    search = _build_transaction_query(patron_pid, status, types)
    if not with_subscription:
        search = search.exclude('terms', type=['subscription'])
    search.aggs.metric('pttr_total_amount', 'sum', field='total_amount')
    search = search[0:0]  # set the from/size to 0 ; no need es hits
    results = search.execute()
    return results.aggregations.pttr_total_amount.value


def get_last_transaction_by_loan_pid(loan_pid, status=None):
    """Return last fee for loan.

    :param loan_pid: the loan pid to search.
    :param status: (optional) the status of transaction.
    :return: return last transaction transaction matching criteria.
    """
    query = PatronTransactionsSearch() \
        .filter('term', loan__pid=loan_pid)
    if status:
        query = query.filter('term', status=status)
    results = query \
        .sort({'creation_date': {'order': 'desc'}}) \
        .source('pid').scan()
    try:
        pid = next(results).pid
        return PatronTransaction.get_record_by_pid(pid)
    except StopIteration:
        return None


def create_patron_transaction_from_overdue_loan(
     loan, dbcommit=True, reindex=True, delete_pid=False):
    """Create a patron transaction for an overdue loan."""
    from ..loans.utils import sum_for_fees
    fees = loan.get_overdue_fees
    total_amount = sum_for_fees(fees)
    if total_amount > 0:
        data = {
            'loan': {
                '$ref': get_ref_for_pid('loans', loan.pid)
            },
            'patron': {
                '$ref': get_ref_for_pid('ptrn', loan.patron_pid)
            },
            'organisation': {
                '$ref': get_ref_for_pid('org', loan.organisation_pid)
            },
            'type': 'overdue',
            'status': 'open',
            'note': _('incremental overdue fees'),
            'total_amount': total_amount,
            'creation_date': datetime.now(timezone.utc).isoformat(),
        }
        steps = [
            {'timestamp': fee[1].isoformat(), 'amount': fee[0]}
            for fee in fees
        ]
        return PatronTransaction.create(
            data,
            dbcommit=dbcommit,
            reindex=reindex,
            delete_pid=delete_pid,
            steps=steps
        )


def create_patron_transaction_from_notification(
     notification=None, dbcommit=None, reindex=None,
     delete_pid=None):
    """Create a patron transaction from notification."""
    from ..notifications.utils import calculate_notification_amount
    total_amount = calculate_notification_amount(notification)
    if total_amount > 0:  # no need to create transaction if amount <= 0 !
        data = {
            'notification': {
                '$ref': get_ref_for_pid('notif', notification.pid)
            },
            'loan': {
                '$ref': get_ref_for_pid('loans', notification.loan_pid)
            },
            'patron': {
                '$ref': get_ref_for_pid('ptrn', notification.patron_pid)
            },
            'organisation': {
                '$ref': get_ref_for_pid(
                    'org',
                    notification.organisation_pid
                )
            },
            'total_amount': total_amount,
            'creation_date': datetime.now(timezone.utc).isoformat(),
            'type': 'overdue',
            'status': 'open'
        }
        return PatronTransaction.create(
            data,
            dbcommit=dbcommit,
            reindex=reindex,
            delete_pid=delete_pid
        )


def create_subscription_for_patron(
     patron, patron_type, start_date, end_date, dbcommit=None, reindex=None,
     delete_pid=None):
    """Create a subscription patron transaction for a patron.

    :param patron: the patron linked to the subscription
    :param patron_type: the patron_type for which we need to create the
                        subscription
    :param start_date: As `datetime`, the starting date of the subscription
    :param end_date: As `datetime`, the ending date of the subscription
    :param dbcommit: is the database must be directly committed.
    :param reindex: is the indexes must be directly updated.
    :param delete_pid: is the database should be cleaned from deleted pids.
    """
    record = {}
    if patron_type.is_subscription_required:
        data = {
            'patron': {
                '$ref': get_ref_for_pid('ptrn', patron.pid)
            },
            'organisation': {
                '$ref': get_ref_for_pid('org', patron.organisation_pid)
            },
            'total_amount': patron_type.get('subscription_amount'),
            'creation_date': datetime.now(timezone.utc).isoformat(),
            'type': 'subscription',
            'status': 'open',
            'note': _("Subscription for '{name}' from {start} to {end}")
            .format(
                name=patron_type.get('name'),
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d')
            )
        }
        record = PatronTransaction.create(
            data,
            dbcommit=dbcommit,
            reindex=reindex,
            delete_pid=delete_pid
        )
    return record
