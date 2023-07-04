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

"""API for manipulating "at_desk" circulation notifications."""

from __future__ import absolute_import, print_function

from rero_ils.filter import format_date_filter
from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.items.dumpers import ItemNotificationDumper
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.dumpers import PatronNotificationDumper
from rero_ils.utils import language_iso639_2to1

from .internal import InternalCirculationNotification


class AtDeskCirculationNotification(InternalCirculationNotification):
    """At_desk circulation notifications class.

    An "at_desk" notification is a message send to a library to notify that an
    item arrives AT_DESK. It's just the same than AVAILABILITY notification
    except that the notification isn't send to the patron but to the
    transaction library.
    Administrator can define a delay between notification creation and
    notification dispatching.

    As one of the purpose of this notification is to be printed, it should
    never be aggregated.
    """

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        An AT_DESK notification can be sent only if a request is done on the
        related item and this request is now in state ITEM_AT_DESK.

        :return: a tuple with two values: a boolean to know if the notification
                 can be cancelled; the reason why the notification can be
                 cancelled (only present if tuple first value is True).
        """
        # Check if parent class would cancel the notification. If yes other
        # check could be skipped.
        can, reason = super().can_be_cancelled()
        if can:
            return can, reason
        # Cancel if no request has been done on corresponding loan.
        request_loan = self.request_loan
        msg = None
        if not request_loan:
            msg = 'No previous request found, none AT_DESK should be sent.'
        # we need to use `!=` comparator because strings was built differently
        # The `!=` operator compares the value or equality of two objects,
        # `is not` operator checks whether two variables point to the same
        # object in memory : `id(str_a) is not `id(str_b)`.
        elif request_loan.get('state') != LoanState.ITEM_AT_DESK:
            msg = "The first found request isn\'t AT_DESK"
        # we don't find any reasons to cancel this notification
        return msg is not None, msg

    def get_template_path(self):
        """Get the template to use to render the notification."""
        return f'email/at_desk/{self.get_language_to_use()}.txt'

    def get_recipients_to(self):
        """Get notification recipient email addresses."""
        # At desk notification will be sent to the loan transaction library.
        if recipient := self.transaction_library.get_email(self.type):
            return [recipient]

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        # Use a delay to be sure the notification is sent AFTER the loan has
        # been indexed (avoid problem due to server load).
        context = {
            'delay': 30
        }
        notifications = notifications or []
        if not notifications:
            return context

        context['loans'] = []
        item_dumper = ItemNotificationDumper()
        patron_dumper = PatronNotificationDumper()
        for notification in notifications:
            loan = notification.loan
            creation_date = format_date_filter(
                notification.get('creation_date'), date_format='medium',
                locale=language_iso639_2to1(notification.get_language_to_use())
            )
            request_expire_date = format_date_filter(
                loan.get('request_expire_date'), date_format='medium',
                locale=language_iso639_2to1(notification.get_language_to_use())
            )
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(
                dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}
            # pickup location name --> !! pickup is on notif.request_loan, not
            # on notif.loan
            request_loan = notification.request_loan
            pickup_location = Location.get_record_by_pid(
                request_loan.get('pickup_location_pid'))
            if not pickup_location:
                pickup_location = Location.get_record_by_pid(
                    request_loan.get('transaction_location_pid'))
            # request_patron
            request_patron = Patron.get_record_by_pid(
                request_loan.get('patron_pid'))

            loan_context = {
                'creation_date': creation_date,
                'document': doc_data,
                'pickup_name': pickup_location.get(
                    'pickup_name', pickup_location.get('name')),
                'request_expire_date': request_expire_date,
                'patron': request_patron.dumps(dumper=patron_dumper)
            }
            context['loans'].append(loan_context)

        return context
