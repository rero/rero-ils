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
from elasticsearch_dsl import Q
from flask import current_app
from invenio_search.api import RecordsSearch

from .models import NotificationIdentifier, NotificationMetadata
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..locations.api import Location
from ..minters import id_minter
from ..patrons.api import Patron
from ..providers import Provider
from ...dispatch import create_dispatch
from ...utils import send_mail

# notif provider
NotificationProvider = type(
    'NotificationProvider',
    (Provider,),
    dict(identifier=NotificationIdentifier, pid_type='notif')
)
# notif minter
notification_id_minter = partial(id_minter, provider=NotificationProvider)
# notif fetcher
notification_id_fetcher = partial(id_fetcher, provider=NotificationProvider)


class NotificationsSearch(RecordsSearch):
    """RecordsSearch for Notifications."""

    class Meta:
        """Search only on Notifications index."""

        index = 'notifications'


class Notification(IlsRecord):
    """Notifications class."""

    minter = notification_id_minter
    fetcher = notification_id_fetcher
    provider = NotificationProvider
    model_cls = NotificationMetadata

    @property
    def organisation_pid(self):
        """Get organisation pid for notification."""
        location_pid = self.replace_refs()['transaction_location']['pid']
        location = Location.get_record_by_pid(location_pid)
        return location.organisation_pid

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Notification record creation."""
        record = super(Notification, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        # create_dispatch(notification=record, delay=False)
        return record

def is_recalled(loan):
    """Check if a recall notification exist already for the given loan."""
    results = NotificationsSearch().filter(
        'term', loan_pid=loan.get('loan_pid')
        ).filter('term', notification_type='recall').source().count()
    return results > 0


def is_availability_created(loan):
    """Check if a availability notification exist already for a loan."""
    results = NotificationsSearch().filter(
        'term', loan_pid=loan.get('loan_pid')
        ).filter('term', notification_type='availability').source().count()
    return results > 0
