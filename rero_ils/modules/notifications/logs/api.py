# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Notification logs API."""

from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.operation_logs.logs.api import SpecificOperationLog

from ..models import RecipientType


class NotificationOperationLog(OperationLog, SpecificOperationLog):
    """Operation log for notification."""

    @classmethod
    def create(cls, data, id_=None, index_refresh='false', **kwargs):
        """Create a new record instance and store it in elasticsearch.

        :param data: Dict with the notification metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :param refresh: If `true` then refresh the affected shards to make
            this operation visible to search, if `wait_for` then wait for a
            refresh to make this operation visible to search, if `false`
            (the default) then do nothing with refreshes.
            Valid choices: true, false, wait_for
        :returns: A new :class:`Record` instance.
        """
        if not (loan := getattr(data, 'loan', None)):
            return

        # If i have no recipients, assign a default value
        # because the "recipients" json schema required at least one item.
        if not (recipients := data.get_recipients(RecipientType.TO)):
            recipients = ['no-recipient-email']
        log = {
            'record': {
                'value': data.get('pid'),
                'type': 'notif'
            },
            'operation': 'create',
            'date': data['creation_date'],
            'loan': {
                'pid': loan.pid,
                'trigger': loan['trigger'],
                'override_flag': False,
                'transaction_channel': 'system',
                'transaction_location': {
                    'pid': loan.transaction_location_pid,
                    'name': cls._get_location_name(
                        loan.transaction_location_pid)
                },
                'pickup_location': {
                    'pid': loan.pickup_location_pid,
                    'name': cls._get_location_name(loan.pickup_location_pid)
                },
                'patron': cls._get_patron_data(loan.patron),
                'item': cls._get_item_data(loan.item)
            },
            'user_name': 'system',
            'notification': {
                'pid': data.pid,
                'type': data['notification_type'],
                'date': data['creation_date'],
                'sender_library_pid': data.library_pid,
                'recipients': recipients
            }
        }

        return super().create(log, index_refresh=index_refresh)
