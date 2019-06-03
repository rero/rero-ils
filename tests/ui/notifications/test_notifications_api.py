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

"""Location Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.api import notification_id_fetcher \
    as fetcher


def test_notification_create(db, es_clear, notification_martigny_data_tmp):
    """Test location creation."""
    notif = Notification.create(
        notification_martigny_data_tmp, delete_pid=True)
    assert notif == notification_martigny_data_tmp
    assert notif.get('pid') == '1'

    notif = Notification.get_record_by_pid('1')
    assert notif == notification_martigny_data_tmp

    fetched_pid = fetcher(notif.id, notif)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'notif'


def test_notification_organisation_pid(
        org_martigny, notification_availabilty_martigny):
    """Test organisation pid has been added during the indexing."""
    search = NotificationsSearch()
    notif = next(search.filter(
        'term', pid=notification_availabilty_martigny.pid).scan())
    record = Notification.get_record_by_pid(notif.pid)
    assert record.organisation_pid == org_martigny.pid


def test_notification_es_mapping(es, db, notification_martigny_data_tmp):
    """Test location elasticsearch mapping."""
    search = NotificationsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Notification.create(
        notification_martigny_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_notification_can_delete(notification_availabilty_martigny):
    """Test notification can delete."""
    assert notification_availabilty_martigny.get_links_to_me() == {}
    assert notification_availabilty_martigny.can_delete
