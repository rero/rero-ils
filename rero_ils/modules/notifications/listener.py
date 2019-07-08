# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2019 RERO.
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

"""Signals connector for Notification."""

from .api import Notification, NotificationsSearch


def enrich_notification_data(sender, json=None, record=None, index=None,
                             **dummy_kwargs):
    """Signal sent before a record is indexed.

    :params json: The dumped record dictionary which can be modified.
    :params record: The record being indexed.
    :params index: The index in which the record will be indexed.
    :params doc_type: The doc_type for the record.
    """
    notification_index_name = NotificationsSearch.Meta.index
    if index.startswith(notification_index_name):
        notification = record
        if not isinstance(record, Notification):
            notification = Notification.get_record_by_pid(record.get('pid'))
        org_pid = notification.organisation_pid
        json['organisation'] = {
            'pid': org_pid
        }
