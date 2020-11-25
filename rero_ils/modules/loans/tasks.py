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

from ..loans.api import anonymize_loans
from ..organisations.api import Organisation


@shared_task(ignore_result=True)
def loan_anonymizer(dbcommit=True, reindex=True):
    """Job to anonymize loans for all organisations.

    :param reindex: reindex the records.
    :param dbcommit: commit record to database.
    :return a count of updated loans.
    """
    loans_count = 0
    for org_pid in Organisation.get_all_pids():
        loans_count_org = anonymize_loans(
            org_pid=org_pid, dbcommit=dbcommit, reindex=reindex)
        loans_count = loans_count + loans_count_org
    msg = 'number_of_loans_anonymized: {loans_count}'.format(
            loans_count=loans_count
    )

    return msg
