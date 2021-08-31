# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

from celery import shared_task
from elasticsearch_dsl import Q

from ..loans.api import Loan, LoansSearch, LoanState
from ..patrons.api import PatronsSearch
from ..utils import set_timestamp


@shared_task(ignore_result=True)
def loan_anonymizer(dbcommit=True, reindex=True):
    """Job to anonymize loans for all organisations.

    :param reindex: reindex the records.
    :param dbcommit: commit record to database.
    :return a count of updated loans.
    """
    query = PatronsSearch() \
        .filter('bool', must_not=[
            Q('exists', field='keep_history'),
            Q('term', keep_history=True)
        ])
    anonym_patron_pids = [h.pid for h in query.source('pid').scan()]
    query = LoansSearch() \
        .filter('terms', patron_pid=anonym_patron_pids) \
        .filter('term', to_anonymize=False) \
        .filter('terms', state=[LoanState.CANCELLED, LoanState.ITEM_RETURNED])
    loan_pids = [h.pid for h in query.source('pid').scan()]

    counter = 0
    for pid in loan_pids:
        loan = Loan.get_record_by_pid(pid)
        if Loan.can_anonymize(loan_data=loan, patron=None):
            loan.anonymize(loan, dbcommit=dbcommit, reindex=reindex)
            counter += 1

    msg = f'number_of_loans_anonymized: {counter}'
    set_timestamp('anonymize-loans', msg=msg)
    return msg
