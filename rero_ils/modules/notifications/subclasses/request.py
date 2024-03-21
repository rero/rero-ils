# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""API for manipulating "request" circulation notifications."""

from __future__ import absolute_import, print_function

from rero_ils.filter import format_date_filter
from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.items.dumpers import ItemNotificationDumper
from rero_ils.modules.loans.api import LoanState
from rero_ils.modules.patrons.dumpers import PatronNotificationDumper
from rero_ils.utils import language_iso639_2to1

from .internal import InternalCirculationNotification


class RequestCirculationNotification(InternalCirculationNotification):
    """Request circulation notifications class.

    A request notification is a message send to a library to notify that a
    document has been requested by a patron. As it's a internal notification,
    it should never be cancelled (except if the requested item doesn't exist
    anymore) and are always send by email.

    Request notification works synchronously. This means it will be send just
    after the creation. This also means that it should never be aggregated.
    """

    def get_recipients_to(self):
        """Get notification email addresses for 'TO' recipient type."""
        # Request notification will be sent to the item location if a location
        # ``notification_email`` attribute is defined, otherwise to the library
        # address.
        if loc_email := self.location.get('notification_email'):
            return [loc_email]
        return super().get_recipients_to()

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        context = {'loans': []}
        notifications = notifications or []

        item_dumper = ItemNotificationDumper()
        patron_dumper = PatronNotificationDumper()
        for notification in notifications:
            loan = notification.loan
            creation_date = format_date_filter(
                notification.get('creation_date'), date_format='medium',
                locale=language_iso639_2to1(notification.get_language_to_use())
            )
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(
                dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}
            # pickup location name
            pickup_location = notification.pickup_location or \
                notification.transaction_location

            loan_context = {
                'creation_date': creation_date,
                'in_transit': loan.state in LoanState.ITEM_IN_TRANSIT,
                'document': doc_data,
                'pickup_name': pickup_location.get(
                    'pickup_name', pickup_location.get('name')),
                'patron': notification.patron.dumps(dumper=patron_dumper)
            }
            context['loans'].append(loan_context)

        return context
