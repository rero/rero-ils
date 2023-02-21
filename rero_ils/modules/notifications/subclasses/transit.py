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

"""API for manipulating "transit" circulation notifications."""

from __future__ import absolute_import, print_function

from rero_ils.filter import format_date_filter
from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.items.dumpers import ItemNotificationDumper
from rero_ils.modules.libraries.dumpers import \
    LibraryCirculationNotificationDumper
from rero_ils.utils import language_iso639_2to1

from .internal import InternalCirculationNotification


class TransitCirculationNotification(InternalCirculationNotification):
    """Transit circulation notifications class.

    A transit notification is a message send to a library to notify that the
    last circulation operation on an item set the item status in TRANSIT model.
    As it's a internal notification, it should never be cancelled (except if
    the requested item doesn't exist anymore) except if the item status isn't
    yet in TRANSIT mode. Always send by email.

    Transit notification works synchronously. This means it will be send just
    after the creation. This also means that it should never be aggregated.
    """

    def get_template_path(self):
        """Get the template to use to render the notification."""
        return f'email/transit_notice/{self.get_language_to_use()}.txt'

    def get_recipients_to(self):
        """Get notification recipient email addresses."""
        # Transit notification will be sent to the loan transaction library.
        if recipient := self.transaction_library.get_email(self.type):
            return [recipient]

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        context = {'loans': []}
        notifications = notifications or []

        item_dumper = ItemNotificationDumper()
        lib_dumper = LibraryCirculationNotificationDumper()
        for notification in notifications:
            trans_lib = notification.transaction_library
            creation_date = format_date_filter(
                notification.get('creation_date'), date_format='medium',
                locale=language_iso639_2to1(notification.get_language_to_use())
            )
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(
                dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}

            loan_context = {
                'creation_date': creation_date,
                'document': doc_data,
                'transaction_library': trans_lib.dumps(dumper=lib_dumper)
            }
            context['loans'].append(loan_context)
        return context
