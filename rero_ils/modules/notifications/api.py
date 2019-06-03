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

from elasticsearch_dsl import Q
from invenio_search.api import RecordsSearch

from .models import NotificationIdentifier, NotificationMetadata
from ..api import IlsRecord
from ..fetchers import id_fetcher
from ..locations.api import Location
from ..minters import id_minter
from ..providers import Provider

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
