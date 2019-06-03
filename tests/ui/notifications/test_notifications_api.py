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

from copy import deepcopy

from utils import flush_index, get_mapping, mock_response

from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch, get_availability_notification
from rero_ils.modules.notifications.api import \
    notification_id_fetcher as fetcher


def test_notification_create(db, es, dummy_notification,
                             loan_validated):
    """Test notification creation, mapping and can_delete."""
    record = deepcopy(dummy_notification)
    del record['pid']
    data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated.get('loan_pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**data)
    record['loan'] = {"$ref": loan_ref}
    notif = Notification.create(
        record,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert notif == record
    assert notif.get('pid') == '1'

    notif = Notification.get_record_by_pid('1')
    assert notif == record

    fetched_pid = fetcher(notif.id, notif)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'notif'

    flush_index(NotificationsSearch.Meta.index)
    assert notif.get_links_to_me() == {}
    assert notif.can_delete
