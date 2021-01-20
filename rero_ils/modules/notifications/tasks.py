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

from .api import Notification
from ..loans.api import get_due_soon_loans, get_overdue_loans
from ..utils import set_timestamp


@shared_task(ignore_result=True)
def process_notifications(verbose=False):
    """Process notifications."""
    result = Notification.process_notifications(verbose=verbose)
    msg = '{info}| send: {send} reject: {reject} error: {error}'.format(
        info='notifications',
        send=result['send'],
        reject=result['reject'],
        error=result['error']
    )
    return msg


@shared_task(ignore_result=True)
def create_over_and_due_soon_notifications(late=True, due_soon=True,
                                           process=True, verbose=False):
    """Creates due soon and late notifications."""
    no_over_due_loans = 0
    no_due_soon_loans = 0
    if due_soon:
        for loan in get_due_soon_loans():
            loan.create_notification(
                notification_type=Notification.DUE_SOON_NOTIFICATION_TYPE)
            no_due_soon_loans += 1
    if late:
        for loan in get_overdue_loans():
            loan.create_notification(
                notification_type=Notification.OVERDUE_NOTIFICATION_TYPE)
            no_over_due_loans += 1

    msg = f'loans| late: {no_over_due_loans} due soon: {no_due_soon_loans}'
    if process:
        msg = '{msg}, {process_msg}'.format(
            msg=msg,
            process_msg=process_notifications.run(verbose=verbose)
        )
    set_timestamp('notification-creation', msg=msg)
    return msg
