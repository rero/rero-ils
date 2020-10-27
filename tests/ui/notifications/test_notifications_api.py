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

from copy import deepcopy

from utils import get_mapping

from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.api import \
    notification_id_fetcher as fetcher
from rero_ils.modules.notifications.dispatcher import Dispatcher


def test_notification_es_mapping(
        dummy_notification, loan_validated_martigny):
    """Test notification elasticsearch mapping."""

    search = NotificationsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping

    notif = deepcopy(dummy_notification)
    notif_data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**notif_data)
    notif['loan'] = {"$ref": loan_ref}

    Notification.create(notif, dbcommit=True, delete_pid=True, reindex=True)

    assert mapping == get_mapping(search.Meta.index)


def test_notification_organisation_pid(
        app, org_martigny, notification_availability_martigny):
    """Test organisation pid has been added during the indexing."""
    assert notification_availability_martigny.organisation_pid == \
        org_martigny.pid

    # test notification can_delete
    assert notification_availability_martigny.get_links_to_me() == {}
    assert notification_availability_martigny.can_delete


def test_notification_create(
        es_clear, dummy_notification, loan_validated_martigny, mailbox):
    """Test notification creation."""
    notif = deepcopy(dummy_notification)
    notif_data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**notif_data)
    notif['loan'] = {"$ref": loan_ref}

    notification = Notification.create(
        notif, dbcommit=True, delete_pid=True, reindex=True)
    assert notification == notif

    pid = notification.get('pid')

    notification = Notification.get_record_by_pid(pid)
    assert notification == notif

    fetched_pid = fetcher(notification.id, notification)
    assert fetched_pid.pid_value == pid
    assert fetched_pid.pid_type == 'notif'

    notification.dispatch(enqueue=False, verbose=True)
    assert len(mailbox) == 1


def test_notification_dispatch(app, mailbox):
    """Test notification dispatch."""

    class DummyNotification(object):

        data = {
            'pid': 'dummy_notification_pid',
            'notification_type': 'dummy_notification'
        }

        def __init__(self, communication_channel):
            self.communication_channel = communication_channel

        def __getitem__(self, key):
            return self.data[key]
            return self.data[key]

        def replace_pids_and_refs(self):
            return {'loan': {
                'pid': 'dummy_notification_loan_pid',
                'patron': {
                    'pid': 'dummy_patron_pid',
                    'patron': {
                        'communication_channel': self.communication_channel
                    }
                }
            }}

        def update_process_date(self):
            return self

    notification = DummyNotification('sms')
    Dispatcher().dispatch_notification(notification=notification, verbose=True)

    notification = DummyNotification('whatsapp')
    Dispatcher().dispatch_notification(notification=notification, verbose=True)

    notification = DummyNotification('mail')
    Dispatcher().dispatch_notification(notification=notification, verbose=True)

    notification = DummyNotification('XXXX')
    Dispatcher().dispatch_notification(notification=notification, verbose=True)
