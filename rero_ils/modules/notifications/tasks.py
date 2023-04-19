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

"""Celery tasks for notification records."""

from __future__ import absolute_import, print_function

from datetime import datetime, timezone

from celery import shared_task
from flask import current_app

from rero_ils.modules.circ_policies.api import OVERDUE_REMINDER_TYPE
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import get_due_soon_loans, get_overdue_loans
from rero_ils.modules.utils import set_timestamp

from .dispatcher import Dispatcher
from .models import NotificationType
from .utils import get_notifications


@shared_task()
def process_notifications(notification_type, verbose=True):
    """Dispatch notifications.

    :param notification_type: notification type to dispatch the notifications.
    :param verbose: is the task should be verbose.
    """
    notification_pids = get_notifications(notification_type=notification_type)
    result = Dispatcher.dispatch_notifications(
        notification_pids=notification_pids,
        verbose=verbose
    )
    set_timestamp(f'notification-dispatch-{notification_type}', **result)
    return result


@shared_task()
def create_notifications(types=None, tstamp=None, verbose=True):
    """Creates requested notifications.

    :param types: an array of notification types to create.
    :param tstamp: a timestamp to specify when the function is execute. By
                   default it will be `datetime.now()`.
    :param verbose: is the task should be verbose.
    """
    from ..loans.utils import get_circ_policy
    types = types or []
    tstamp = tstamp or datetime.now(timezone.utc)
    logger = current_app.logger
    notification_counter = {}

    # DUE SOON NOTIFICATIONS
    if NotificationType.DUE_SOON in types:
        notification_counter[NotificationType.DUE_SOON] = 0
        logger.debug("DUE_SOON_NOTIFICATION_CREATION -------------")
        for loan in get_due_soon_loans(tstamp=tstamp):
            try:
                logger.debug(f"* Loan#{loan.pid} is considered as 'due_soon'")
                notifications = loan.create_notification(
                    _type=NotificationType.DUE_SOON)
                notification_counter[NotificationType.DUE_SOON] += len(
                    notifications)
            except Exception as error:
                logger.error(
                    f'Unable to create DUE_SOON notification :: {error}',
                    exc_info=True, stack_info=True
                )
        process_notifications(NotificationType.DUE_SOON)
    # OVERDUE NOTIFICATIONS
    if NotificationType.OVERDUE in types:
        logger.debug("OVERDUE_NOTIFICATION_CREATION --------------")
        notification_counter[NotificationType.OVERDUE] = 0
        for loan in get_overdue_loans(tstamp=tstamp):
            logger.debug(f"* Loan#{loan.pid} is considered as 'overdue'")
            # For each overdue loan, we need to get the 'overdue' reminders
            # to should be sent from the due_date and the current used date.
            loan_library = Library.get_record_by_pid(loan.library_pid)
            open_days = loan_library.count_open(
                start_date=loan.overdue_date,
                end_date=tstamp
            )
            circ_policy = get_circ_policy(loan)
            logger.debug(f'  - this loan use the cipo#{circ_policy.pid}')
            logger.debug(f'  - open days from loans due_date :: {open_days}')
            reminders = circ_policy.get_reminders(
                reminder_type=OVERDUE_REMINDER_TYPE,
                limit=open_days
            )
            # For each reminder, try to create it.
            #   the `create_notification` method will check if the notification
            #   is already sent. If the notification has already sent, it will
            #   not be created again
            for idx, _ in enumerate(reminders):
                try:
                    if notifications := loan.create_notification(
                        _type=NotificationType.OVERDUE,
                        counter=idx
                    ):
                        msg = f'  --> Overdue notification#{idx+1} created'
                        logger.debug(msg)
                        notification_counter[NotificationType.OVERDUE] += len(
                            notifications)

                    else:
                        msg = f'  --> Overdue notification#{idx+1} skipped ' \
                              ':: already sent'
                        logger.debug(msg)
                except Exception as error:
                    logger.error(
                        f'Unable to create OVERDUE notification :: {error}',
                        exc_info=True, stack_info=True
                    )
        process_notifications(NotificationType.OVERDUE)
    notification_sum = sum(notification_counter.values())

    counters = {k: v for k, v in notification_counter.items() if v > 0}
    if verbose:
        logger = current_app.logger
        logger.info("NOTIFICATIONS CREATION TASK")
        logger.info(f'  * total of {notification_sum} notification(s) created')
        for notif_type, cpt in counters.items():
            logger.info(f'  +--> {cpt} `{notif_type}` notification(s) created')

    return counters
