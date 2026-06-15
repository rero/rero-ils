# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating "request" circulation notifications."""

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
        if loc_email := self.location.get("notification_email"):
            return [loc_email]
        return super().get_recipients_to()

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        context = {"loans": []}
        notifications = notifications or []

        item_dumper = ItemNotificationDumper()
        patron_dumper = PatronNotificationDumper()
        for notification in notifications:
            loan = notification.loan
            creation_date = format_date_filter(
                notification.get("creation_date"),
                date_format="medium",
                locale=language_iso639_2to1(notification.get_language_to_use()),
            )
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}
            # pickup location name
            pickup_location = notification.pickup_location or notification.transaction_location

            loan_context = {
                "creation_date": creation_date,
                "in_transit": loan.state in LoanState.ITEM_IN_TRANSIT,
                "document": doc_data,
                "pickup_name": pickup_location.get("pickup_name", pickup_location.get("name")),
                "patron": notification.patron.dumps(dumper=patron_dumper),
            }
            context["loans"].append(loan_context)

        return context
