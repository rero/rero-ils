# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""API for dispatch Notifications."""

from __future__ import absolute_import, print_function

from flask import current_app
from invenio_mail.api import TemplatedMessage
from invenio_mail.tasks import send_email as task_send_email
from num2words import num2words

from .api import Notification
from .models import NotificationChannel, NotificationType
from .utils import exists_similar_notification, \
    get_communication_channel_to_use, get_template_to_use
from ..items.models import ItemStatus
from ..libraries.api import email_notification_type
from ..locations.api import Location
from ..patrons.api import Patron
from ...filter import format_date_filter
from ...utils import language_iso639_2to1


class Dispatcher:
    """Dispatcher notifications class."""

    @classmethod
    def dispatch_notifications(cls, notification_pids=None, resend=False,
                               verbose=False):
        """Dispatch the notification.

        :param notification_pids: Notification pids to send.
        :param resend: Resend notification if already send.
        :param verbose: Verbose output.
        :returns: dictionary with processed and send count
        """
        def get_dispatcher_function(channel):
            try:
                communication_switcher = current_app.config.get(
                    'RERO_ILS_COMMUNICATION_DISPATCHER_FUNCTIONS', [])
                return communication_switcher[channel]
            except KeyError:
                current_app.logger.warning(
                    f'The communication channel: {channel}'
                    ' is not yet implemented')
                return Dispatcher.not_yet_implemented

        sent = not_sent = 0
        aggregated = {}
        pids = notification_pids if notification_pids else []
        notifications = [Notification.get_record_by_pid(pid) for pid in pids]
        notifications = list(filter(None, notifications))
        # BUILD AGGREGATED NOTIFICATIONS
        #   Notifications should be aggregated on (in this order):
        #     1. notification_type,
        #     2. communication_channel
        #     3. library
        #     4. patron
        errors = 0
        for notification in notifications:
            try:
                cls._process_notification(
                    notification, resend, aggregated)
            except Exception as error:
                errors += 1
                current_app.logger.error(
                    f'Notification has not be sent (pid: {notification.pid},'
                    f' type: {notification["notification_type"]}): '
                    f'{error}', exc_info=True, stack_info=True)

        # SEND AGGREGATED NOTIFICATIONS
        for notification_type, notification_values in aggregated.items():
            for comm_channel, channel_values in notification_values.items():
                # find the dispatcher function to use for this channel.
                dispatcher_function = get_dispatcher_function(comm_channel)
                for library_pid, library_values in channel_values.items():
                    for patron_pid, ctx_data in library_values.items():
                        if verbose:
                            current_app.logger.info(
                                f'Dispatch notifications: {notification_type} '
                                f'library: {library_pid} '
                                f'patron: {patron_pid} '
                                f'documents: {len(ctx_data["documents"])}'
                            )
                        result = dispatcher_function(ctx_data)
                        for notification in ctx_data['notifications']:
                            notification.update_process_date(sent=result)
                        if result:
                            sent += len(ctx_data['notifications'])
                        else:
                            not_sent += len(ctx_data['notifications'])
        return {
            'processed': len(notifications),
            'sent': sent,
            'not_sent': not_sent,
            'errors': errors
        }

    @classmethod
    def _process_notification(cls, notification, resend, aggregated):
        """Process one notification.

        :param notification: Notification to process.
        :param resend: Resend notification if already send.
        :param aggregated: Dict to store notification results.
        :returns: A dispatcher function.
        """
        from ..items.api import Item
        from ..loans.api import LoanState

        n_type = notification['notification_type']
        process_date = notification.get('process_date')

        # 1. Check if notification has already been processed and if we
        #    need to resend it. If not, skip this notification and continue
        if process_date:
            current_app.logger.warning(
                f'Notification: {notification.pid} already processed '
                f'on: {process_date}'
            )
            if not resend:
                return

        data = notification.replace_pids_and_refs()
        loan = data['loan']

        item_data = loan.get('item')
        item = Item.get_record_by_pid(item_data.get('pid'))

        # 2. Check if we really need to process the notifications in the case
        #    of asynchronous notifications. If not, then update the
        #    notification 'status' and stop the notification processing.
        can_cancel, reason = Dispatcher._can_cancel_notification(data, item)
        if can_cancel:
            msg = f'Notification #{notification.pid} cancelled: {reason}'
            current_app.logger.info(msg)
            notification.update_process_date(sent=False, status='cancelled')
            return

        # 3. Find the communication channel to use to dispatch this
        #    notification. The channel depends on the loan, the
        #    notification type and the related patron
        patron = loan['patron']
        communication_channel = get_communication_channel_to_use(
            loan,
            notification,
            patron
        )

        # 4. Get the communication language to use. Except for internal
        #    notification, the language to use is defined into the related
        #    patron account. For Internal notifications, the language is
        #    the library defined language.
        communication_lang = patron['patron']['communication_language']
        if n_type in NotificationType.INTERNAL_NOTIFICATIONS:
            communication_lang = loan['library']['communication_language']
        language = language_iso639_2to1(communication_lang)

        # 5. Compute the reminder counter.
        #    For some notification (overdue, ...) the reminder counter is
        #    an information to use into the message to send. We need to
        #    translate this counter into a localized string.
        reminder_counter = data.get('reminder_counter', 0)
        reminder = reminder_counter + 1
        reminder = num2words(reminder, to='ordinal', lang=language)

        # 6. Get the template to use for the notification.
        #    Depending of the notification and the reminder counter, find
        #    the correct template file to use.
        tpl_path = get_template_to_use(
            loan, n_type, reminder_counter).rstrip('/')
        template = f'{tpl_path}/{communication_lang}.txt'

        # 7. Build the context to use to render the template.
        ctx_data = {
            'notification_type': n_type,
            'creation_date': format_date_filter(
                notification.get('creation_date'),
                date_format='medium',
                locale=language
            ),
            'in_transit': loan['state'] in [
                LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
            ],
            'template': template,
            'profile_url': loan['profile_url'],
            'patron': patron,
            'library': loan['library'],
            'pickup_library': loan['pickup_library'],
            'transaction_library': loan['transaction_library'],
            'pickup_name': loan['pickup_name'],
            'documents': [],
            'notifications': []
        }
        transaction_location = loan.get('transaction_location')
        if transaction_location:
            ctx_data['transaction_location_name'] = \
                transaction_location['name']

        # aggregate notifications
        l_pid = loan['library']['pid']
        p_pid = patron['pid']
        c_channel = communication_channel

        documents_data = {
            'title_text': loan['document']['title_text'],
            'responsibility_statement':
                loan['document']['responsibility_statement'],
            'reminder': reminder,
            'end_date': loan.get('end_date')
        }
        documents_data = {k: v for k, v in documents_data.items() if v}

        # Add item to document
        if item_data:
            if n_type in [
                NotificationType.BOOKING,
                NotificationType.AVAILABILITY
            ]:
                # get the requested loan it can be in several states
                # due to the automatic request validation
                request_loan = None
                for state in [
                    LoanState.ITEM_AT_DESK,
                    LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
                    LoanState.PENDING
                ]:
                    request_loan = item.get_first_loan_by_state(state)
                    if request_loan:
                        break
                request_patron = Patron.get_record_by_pid(
                    request_loan['patron_pid'])
                ctx_data['request_patron'] = \
                    request_patron.replace_refs().dumps()
                pickup_location = Location.get_record_by_pid(
                    request_loan['pickup_location_pid'])
                if pickup_location:
                    ctx_data['request_pickup_name'] = \
                        pickup_location['pickup_name']
                else:
                    transaction_location = Location.get_record_by_pid(
                        request_loan['transaction_location_pid'])
                    ctx_data['request_pickup_name'] = \
                        transaction_location['name']

            documents_data['item'] = {
                'barcode': item_data['barcode'],
                'call_number': item_data.get('call_number'),
                'second_call_number': item_data.get('second_call_number')
            }
            documents_data['item'] = \
                {k: v for k, v in documents_data['item'].items() if v}
            location = item_data.get('location')
            if location:
                loc = Location.get_record_by_pid(location.get('pid'))
                lib = loc.get_library()
                documents_data['item']['location_name'] = loc.get('name')
                documents_data['item']['library_name'] = lib.get('name')
                email = loc.get('notification_email')
                if email:
                    ctx_data['location_email'] = email

        # Needs to be at the end of the function to avoid to send notification
        # in case of error
        aggregated.setdefault(n_type, {})
        aggregated[n_type].setdefault(c_channel, {})
        aggregated[n_type][c_channel].setdefault(l_pid, {})
        aggregated[n_type][c_channel][l_pid].setdefault(p_pid, ctx_data)

        # Add information into correct aggregations
        aggregation = aggregated[n_type][c_channel][l_pid][p_pid]
        aggregation['documents'].append(documents_data)
        aggregation['notifications'].append(notification)

    @staticmethod
    def _can_cancel_notification(data, item):
        """Check if a notification must be be cancelled.

        As notification process could be asynchronous, in some case, when the
        notification is processed, it's not anymore required to be sent.
        By example, an AVAILABLE notification must not be sent if the
        related loan item is already in ON_LOAN state.

        :param data: the notification data to check.
        :param item: the notification related item
        :return True if the notification can be cancelled, False otheriwse.
        """
        n_type = data['notification_type']
        loan = data['loan']

        # The very first check is to know if the related item still exists.
        # If not, no need to check other conditions.
        if not item:
            return True, "Item doesn't exists anymore"

        # a) we don't need to check INTERNAL_NOTIFICATION. These notifications
        #    are sent to library and are synchronously dispatched.
        # b.1) Special case for RECALL notification: If the related loan isn't
        #      ON_LOAN state anymore, we doesn't need to process it.
        # b.2) For OVERDUE and DUE_SOON notification, check that no other
        #      corresponding notification has already been sent.
        # b.3) Otherwise, check if the notification type is available into
        #      notification candidates related to the loan. If not, the
        #      notification can be cancelled.
        if n_type not in NotificationType.INTERNAL_NOTIFICATIONS:
            if n_type == NotificationType.RECALL:
                if item.status != ItemStatus.ON_LOAN:
                    return True, "Item isn't anymore ON_LOAN state"
            elif n_type in NotificationType.REMINDERS_NOTIFICATIONS:
                if exists_similar_notification(data):
                    return True, 'Similar notification already proceed'
            else:
                # unpack tuple's notification candidate
                candidates_types = [
                    n[1] for n in
                    loan.get_notification_candidates(trigger=None)
                ]
                if n_type not in candidates_types:
                    msg = "Notification type isn't into notification candidate"
                    return True, msg
        return False, None

    @staticmethod
    def _create_email(recipients, reply_to, ctx_data, template):
        """Create email message from template.

        :param recipients: List of emails to send the message too.
        :param reply_to: Reply to email address.
        :param ctx_data: Dictionary with informations used in template.
        :param template: Template to use to create TemplatedMessage.
        :returns: Message created.
        """
        msg = TemplatedMessage(
            template_body=template,
            sender=current_app.config.get('DEFAULT_SENDER_EMAIL',
                                          'noreply@rero.ch'),
            reply_to=reply_to,
            recipients=recipients,
            ctx=ctx_data
        )
        # subject is the first line, body is the rest
        text = msg.body.split('\n')
        msg.subject = text[0]
        msg.body = '\n'.join(text[1:])
        return msg

    @staticmethod
    def not_yet_implemented(*args):
        """Do nothing placeholder for a notification."""
        return True

    @staticmethod
    def send_mail_for_printing(ctx_data):
        """Send the notification by email to the library.

        :param ctx_data: Dictionary with informations used in template.
        """
        notification_type = ctx_data['notification_type']

        # 1. Find the library email were to send the message.
        #   - for BOOKING and TRANSIT, we need to use the transaction library
        #   - for other notifications, we need to use library
        library = ctx_data['library']
        if ctx_data['notification_type'] in [
            NotificationType.BOOKING,
            NotificationType.TRANSIT_NOTICE
        ]:
            library = ctx_data['transaction_library']
        library_email = email_notification_type(library, notification_type)

        # 2. For a REQUEST notification we mainly need to use the email define
        #    on the location. If the location email isn't defined, then use the
        #    library email by default.
        notification_email = library_email
        if notification_type == NotificationType.REQUEST:
            notification_email = ctx_data.get('location_email', library_email)

        # 3. Force patron communication channel to 'mail'
        #    In some cases we force the notification to be send by mail despite
        #    the patron asked to received them by email (cipo reminders
        #    notifications with a communication channel to 'mail' value).
        #    So we need to hack the patron profile communication channel to
        #    'mail' value to include the address text block into message.
        ctx_data['patron']['patron']['communication_channel'] = \
            NotificationChannel.MAIL

        error_reasons = []
        reply_to = ctx_data['library'].get('email')
        if not notification_email:
            error_reasons.append('Missing notification email')
        if not reply_to:
            error_reasons.append('Missing reply_to email')
        if error_reasons:
            current_app.logger.warning(
                'Notification for printing is lost for patron: '
                f'{ctx_data["patron"]["pid"]} '
                f'send to library: {ctx_data["library"]["pid"]} '
                f'({")(".join(error_reasons)})')
            return False

        msg = Dispatcher._create_email(
            recipients=[notification_email],
            reply_to=reply_to,
            ctx_data=ctx_data,
            template=ctx_data['template']
        )
        task_send_email.apply_async((msg.__dict__,))
        return True

    @staticmethod
    def send_mail_to_patron(ctx_data):
        """Send the notification by email to the patron.

        :param ctx_data: Dictionary with informations used in template.
        """
        # get the recipient email from loan.patron.patron.email
        error_reasons = []
        patron = ctx_data['patron']
        reply_to = ctx_data['library'].get('email')
        recipients = list(filter(None, [
            patron.get('email'),
            patron['patron'].get('additional_communication_email')
        ]))
        if not recipients:
            error_reasons.append('Missing notification recipients')
        if not reply_to:
            error_reasons.append('Missing reply_to email')
        if error_reasons:
            current_app.logger.warning(
                'Notification is lost for patron: '
                f'{ctx_data["patron"]["pid"]} '
                f'send to library: {ctx_data["library"]["pid"]} '
                f'({")(".join(error_reasons)})')
            return False

        # get availability delay
        delay_availability = 0
        for setting in ctx_data['library']['notification_settings']:
            if setting['type'] == NotificationType.AVAILABILITY:
                delay_availability = setting.get('delay', 0)

        msg = Dispatcher._create_email(
            recipients=recipients,
            reply_to=reply_to,
            ctx_data=ctx_data,
            template=ctx_data['template']
        )
        task_send_email.apply_async(
            (msg.__dict__,),
            countdown=delay_availability
        )
        return True
