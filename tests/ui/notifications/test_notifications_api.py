# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Notification Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

from utils import get_mapping

from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.api import \
    notification_id_fetcher as fetcher


def test_notification_organisation_pid(
        org_martigny, notification_availability_martigny):
    """Test organisation pid has been added during the indexing."""
    search = NotificationsSearch()
    pid = notification_availability_martigny.get('pid')
    notification = next(search.filter('term', pid=pid).scan())
    assert notification.organisation.pid == org_martigny.pid

    # test notification can_delete
    assert notification_availability_martigny.get_links_to_me() == {}
    assert notification_availability_martigny.can_delete


def test_notification_es_mapping(
        dummy_notification, loan_validated_martigny):
    """Test notification elasticsearch mapping."""

    search = NotificationsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping

    notif = deepcopy(dummy_notification)
    notif_data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('loan_pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**notif_data)
    notif['loan'] = {"$ref": loan_ref}

    Notification.create(notif, dbcommit=True, delete_pid=True, reindex=True)

    assert mapping == get_mapping(search.Meta.index)


def test_notification_create(
        es_clear, dummy_notification, loan_validated_martigny, mailbox):
    """Test notification creation."""
    notif = deepcopy(dummy_notification)
    notif_data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('loan_pid')
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

    notification.dispatch()
    assert len(mailbox) == 1
