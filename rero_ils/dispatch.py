# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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

"""API for manipulating Notifications."""

from __future__ import absolute_import, print_function

from functools import partial

from celery import shared_task

from .modules.patrons.api import Patron
from .utils import send_mail


class Dispatch():
    """Dispatch notifications class."""

    @classmethod
    def send_notification(cls, notification=None):
        """Send notifications class."""
        from .modules.items.api import Item        
        
        if notification:
            record = notification.replace_refs()
            patron_pid = record['patron']['pid']
            recipient = Patron.get_record_by_pid(patron_pid).get('email')
            item_pid = record['item']['pid']
            item = Item.get_record_by_pid(item_pid).replace_refs()
            document_pid = item.get('document', {}).get('pid')
            print(
                'Sending email: {patron_pid} {notification_pid}'.format(
                    patron_pid=patron_pid,
                    notification_pid=record.get('pid')
                )
            )
            # send_mail(
            #     subject=notification.get('notification_type'),
            #     recipients=recipient,
            #     template='library notification',
            #     language='eng',
            #     document=document_pid
            # )


def create_dispatch(notification, delay=True):
    """Create async dispatch notification."""
    if delay:
        create_dispatch_task.delay(notification=notification)
    else:
        create_dispatch_task(notification=notification)


@shared_task(ignore_result=True)
def create_dispatch_task(notification):
    """Create Dispatch notification."""
    Dispatch.send_notification(notification=notification)
