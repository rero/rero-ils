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

"""Notification Record tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.notifications.dispatcher import Dispatcher
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.subclasses.availability import \
    AvailabilityCirculationNotification


def test_notification_organisation_pid(
        app, org_martigny, notification_availability_martigny):
    """Test organisation pid has been added during the indexing."""
    assert notification_availability_martigny.organisation_pid == \
        org_martigny.pid

    # test notification can_delete
    can, reasons = notification_availability_martigny.can_delete
    assert can
    assert reasons == {}


def test_notification_mail(notification_late_martigny, lib_martigny, mailbox):
    """Test notification creation.
        Patron communication channel is mail.
    """
    mailbox.clear()
    Dispatcher.dispatch_notifications(notification_late_martigny['pid'])
    recipient = lib_martigny.get_email(
        notification_late_martigny['notification_type'])
    assert recipient
    assert mailbox[0].recipients == [recipient]


def test_notification_email(notification_late_sion, patron_sion, mailbox):
    """Test overdue notification.
        Patron communication channel is email.
    """
    mailbox.clear()
    Dispatcher.dispatch_notifications(notification_late_sion['pid'])
    assert mailbox[0].recipients == [patron_sion.dumps()['email']]


def test_notification_email_availability(notification_availability_sion,
                                         lib_sion, patron_sion, mailbox):
    """Test availability notification.
        Patron communication channel is email.
    """
    # test availability context fields
    context = AvailabilityCirculationNotification.get_notification_context(
        notifications=[notification_availability_sion]
    )
    for key in ['delay', 'library', 'loans', 'patron']:
        assert key in context

    loan_ctx = context['loans'][0]
    for key in ['document', 'pickup_name', 'pickup_until']:
        assert key in loan_ctx
    for key in ['barcode', 'call_numbers', 'library_name', 'location_name',
                'title_text']:
        assert key in loan_ctx['document']
    for key in ['address', 'barcode', 'first_name', 'last_name']:
        assert key in context['patron']

    mailbox.clear()
    Dispatcher.dispatch_notifications(notification_availability_sion['pid'])
    assert mailbox[0].recipients == [patron_sion.dumps()['email']]


def test_notification_email_aggregated(notification_availability_martigny,
                                       notification2_availability_martigny,
                                       lib_martigny, patron_martigny, mailbox):
    """Test availability notification.
        Patron communication channel is email.
    """
    mailbox.clear()
    Dispatcher.dispatch_notifications([
        notification_availability_martigny['pid'],
        notification2_availability_martigny['pid']
    ], verbose=True)
    assert len(mailbox) == 1

    recipient = '???'
    for notification_setting in lib_martigny.get('notification_settings'):
        if notification_setting['type'] == NotificationType.AVAILABILITY:
            recipient = notification_setting['email']
    assert mailbox[0].recipients == [recipient]
