# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Utilities functions for notifications."""
import ciso8601
from elasticsearch_dsl import Q

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE, \
    OVERDUE_REMINDER_TYPE, CircPolicy
from rero_ils.modules.locations.api import Location
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.notifications.models import NotificationType


def get_notification(loan, notification_type):
    """Returns specific notification from loan.

    :param loan: the parent loan.
    :param notification_type: the type of notification sent.
    """
    from .api import Notification
    results = NotificationsSearch()\
        .filter('term', context__loan__pid=loan.pid)\
        .filter('term', notification_type=notification_type) \
        .params(preserve_order=True) \
        .sort({'creation_date': {"order": "desc"}}) \
        .source().scan()
    try:
        pid = next(results).pid
        return Notification.get_record_by_pid(pid)
    except StopIteration:
        return None


def get_notifications(notification_type, processed=False, not_sent=False):
    """Returns specific notifications pids.

    :param notification_type: filter on the notification type.
    :param processed: filter on already processed notifications.
    :param not_sent: filter on not yet send notifications.
    :return a notification pid generator.
    """
    query = NotificationsSearch()\
        .filter('term', notification_type=notification_type) \
        .source('pid')
    if not not_sent:
        query = query.filter(
            'bool', must_not=[
                Q('exists', field='notification_sent'),
                Q('term', notification_sent=False)
            ]
        )
    if processed:
        query = query.filter('exists', field='process_date')
    else:
        query = query.filter(
            'bool', must_not=[Q('exists', field='process_date')])

    for hit in query.scan():
        yield hit.pid


def number_of_notifications_sent(loan,
                                 notification_type=NotificationType.OVERDUE):
    """Get the number of notifications sent for the given loan.

    :param loan: the parent loan.
    :param notification_type: the type of notification to find.
    :return notification counter.
    """
    trans_date = ciso8601.parse_datetime(loan.get('transaction_date'))
    return NotificationsSearch()\
        .filter('term', context__loan__pid=loan.pid)\
        .filter('term', notification_type=notification_type) \
        .filter('term', notification_sent=True) \
        .filter('range', creation_date={'gt': trans_date}) \
        .source().count()


def calculate_notification_amount(notification):
    """Return amount due for a notification.

    :param notification: the notification for which to compute the amount. At
                         this time, this is not yet a `Notification`, only a
                         dict of structured data.
    :return the amount due for this notification. 0 if no amount could be
            compute.
    """
    # Find the reminder type to use based on the notification that we would
    # sent. If no reminder type is found, then no amount could be calculated
    # and we can't return '0'
    notif_type = notification.get('notification_type')
    reminder_type_mapping = {
        NotificationType.DUE_SOON: DUE_SOON_REMINDER_TYPE,
        NotificationType.OVERDUE: OVERDUE_REMINDER_TYPE
    }
    reminder_type = reminder_type_mapping.get(notif_type)
    if not notif_type or not reminder_type:
        return 0

    # to find the notification due amount, we firstly need to get the
    # circulation policy linked to the parent loan.
    location_pid = notification.transaction_location_pid
    location = Location.get_record_by_pid(location_pid)
    cipo = CircPolicy.provide_circ_policy(
        location.organisation_pid,
        location.library_pid,
        notification.patron.patron_type_pid,
        notification.item.holding_circulation_category_pid
    )

    # now we get the circulation policy, search the correct reminder depending
    # of the reminder_counter from the notification context.
    reminder = cipo.get_reminder(
        reminder_type=reminder_type,
        idx=notification.get('context', {}).get('reminder_counter', 0)
    )
    return reminder.get('fee_amount', 0) if reminder else 0
