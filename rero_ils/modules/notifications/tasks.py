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

"""Celery tasks for notification records."""

from __future__ import absolute_import, print_function

from celery import shared_task

from ..loans.api import get_due_soon_loans, get_overdue_loans


@shared_task(ignore_result=True)
def create_over_and_due_soon_notifications():
    """Creates due_soon and overdue notifications."""
    over_due_loans = get_overdue_loans()
    no_over_due_loans = 0
    for loan in over_due_loans:
        loan.create_notification(notification_type='overdue')
        no_over_due_loans += 1

    due_soon_loans = get_due_soon_loans()
    no_due_soon_loans = 0
    for loan in due_soon_loans:
        loan.create_notification(notification_type='due_soon')
        no_due_soon_loans += 1

    return 'created {no_over_due_loans} overdue loans, '\
        '{no_due_soon_loans} due soon loans'.format(
            no_over_due_loans=no_over_due_loans,
            no_due_soon_loans=no_due_soon_loans)
