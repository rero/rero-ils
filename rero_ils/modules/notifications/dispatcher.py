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

from ..libraries.api import email_notification_type
from ..locations.api import Location
from ..notifications.api import Notification
from ...filter import format_date_filter
from ...utils import language_iso639_2to1


class Dispatcher:
    """Dispatcher notifications class."""

    @classmethod
    def dispatch_notifications(cls, notification_pids=None, resend=False,
                               verbose=False):
        """Dispatch the notification.

        :param notification_pids: Notification pids to send notification.
        :param resend: Resend notification if already send.
        :param verbose: Verbose output.
        :returns: dictionary with proccessed and send count
        """
        from .api import Notification, get_communication_channel_to_use, \
            get_template_to_use
        from ..items.api import Item
        from ..loans.api import LoanState
        from ..patrons.api import Patron

        def not_yet_implemented(*args):
            """Do nothing placeholder for a notification."""
            return

        sent = not_sent = count = 0
        aggregated = {}
        notification_pids = notification_pids if notification_pids else []
        for notification_pid in notification_pids:
            count += 1
            notification = Notification.get_record_by_pid(notification_pid)
            if notification:
                notification_type = notification['notification_type']
                process_date = notification.get('process_date')
                if process_date:
                    current_app.logger.warning(
                        f'Notification: {notification.pid} already processed '
                        f'on: {process_date}'
                    )
                    if not resend:
                        continue
                communication_switcher = {
                    'email': Dispatcher.send_mail_to_patron,
                    'mail': Dispatcher.send_mail_for_printing,
                    #  'sms': not_yet_implemented
                    #  'telepathy': self.madness_mind
                    #  ...
                }
                data = notification.replace_pids_and_refs()
                loan = data['loan']
                patron = loan['patron']
                communication_channel = get_communication_channel_to_use(
                    loan, notification, patron
                )
                dispatcher_function = communication_switcher.get(
                    communication_channel,
                    not_yet_implemented
                )
                reminder_counter = data.get('reminder_counter', 0)
                reminder = reminder_counter + 1

                if notification_type in [
                    Notification.BOOKING_NOTIFICATION_TYPE,
                    Notification.REQUEST_NOTIFICATION_TYPE,
                    Notification.TRANSIT_NOTICE_NOTIFICATION_TYPE
                ]:
                    # Library notification
                    communication_lang =\
                        data['loan']['library']['communication_language']
                else:
                    # Patron notification
                    communication_lang =\
                        patron['patron']["communication_language"]

                language = language_iso639_2to1(communication_lang)
                reminder = num2words(
                    reminder,
                    to='ordinal',
                    lang=language
                )
                if dispatcher_function == not_yet_implemented:
                    current_app.logger.warning(
                        'The communication channel of the patron'
                        f' (pid: {patron["pid"]}) is not yet implemented')
                # loan = Loan.get_record_by_pid(loan['pid'])
                tpl_path = get_template_to_use(
                    loan, notification_type, reminder_counter).rstrip('/')
                template = f'{tpl_path}/{communication_lang}.txt'
                # Add all information used in the templates here:
                ctx_data = {
                    'notification_type': notification_type,
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
                n_type = notification_type
                l_pid = loan['library']['pid']
                p_pid = patron['pid']
                aggregated.setdefault(n_type, {})
                aggregated[n_type].setdefault(l_pid, {})
                aggregated[n_type][l_pid].setdefault(p_pid, ctx_data)
                documents_data = {
                    'title_text': loan['document']['title_text'],
                    'responsibility_statement':
                        loan['document']['responsibility_statement'],
                    'reminder': reminder
                }
                end_date = loan.get('end_date')
                if end_date:
                    documents_data['end_date'] = end_date
                # Add item to document
                item_data = loan.get('item')
                if item_data:
                    if notification_type in [
                        Notification.BOOKING_NOTIFICATION_TYPE,
                        Notification.AVAILABILITY_NOTIFICATION_TYPE
                    ]:
                        # get item from the checkin loan
                        item = Item.get_record_by_pid(
                            item_data.get('pid'))
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
                        ctx_data['request_pickup_name'] = \
                            pickup_location['pickup_name']
                    documents_data['item'] = {
                        'barcode': item_data['barcode']
                    }
                    call_number = item_data.get('call_number')
                    if call_number:
                        documents_data['item']['call_number'] = call_number
                    second_call_number = item_data.get('second_call_number')
                    if second_call_number:
                        documents_data['item']['second_call_number'] = \
                            second_call_number
                    location = item_data.get('location')
                    if location:
                        loc = Location.get_record_by_pid(location.get('pid'))
                        email = loc.get('notification_email')
                        if email:
                            ctx_data['location_email'] = email
                        documents_data['item']['location_name'] =\
                            loc.get('name')
                        library = loc.get_library()
                        documents_data['item']['library_name'] =\
                            library.get('name')

                aggregated[n_type][l_pid][p_pid]['documents'].append(
                    documents_data
                )
                aggregated[n_type][l_pid][p_pid]['notifications'].append(
                    notification
                )

        for notification_type, notification_values in aggregated.items():
            for library_pid, library_values in notification_values.items():
                for patron_pid, ctx_data in library_values.items():
                    if verbose:
                        current_app.logger.info(
                            f'Dispatch notifications: {notification_type} '
                            f'library: {library_pid} '
                            f'patron: {patron_pid} '
                            f'documents: {len(ctx_data["documents"])}'
                        )
                    sent = dispatcher_function(ctx_data)
                    for notification in ctx_data['notifications']:
                        notification.update_process_date(sent=sent)
                    if sent:
                        sent += len(ctx_data['notifications'])
                    else:
                        not_sent += len(ctx_data['notifications'])
        return {'processed': count, 'sent': sent, 'not_sent': not_sent}

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
        text = msg.body.split('\n')
        # subject is the first line
        msg.subject = text[0]
        # body
        msg.body = '\n'.join(text[1:])
        return msg

    @staticmethod
    def send_mail_for_printing(ctx_data):
        """Send the notification by email to the library.

        :param ctx_data: Dictionary with informations used in template.
        """
        library = ctx_data['library']
        if ctx_data['notification_type'] in [
            Notification.BOOKING_NOTIFICATION_TYPE,
            Notification.TRANSIT_NOTICE_NOTIFICATION_TYPE
        ]:
            library = ctx_data['transaction_library']
        library_email = email_notification_type(
            library,
            ctx_data['notification_type']
        )
        if ctx_data['notification_type'] == \
                Notification.REQUEST_NOTIFICATION_TYPE:
            # For the request type, we search the email address
            # on the location and then on the library
            email = ctx_data.get('location_email')
            notification_email = email if email else library_email
        else:
            # get the recipient email from the library
            notification_email = library_email
        error_reason = ''
        if not notification_email:
            error_reason = '(Missing notification email)'
        reply_to = ctx_data['library'].get('email')
        if not reply_to:
            error_reason = '(Missing reply_to email)'
        if error_reason:
            current_app.logger.warning(
                'Notification for printing is lost for patron: '
                f'{ctx_data["patron"]["pid"]} '
                f'send to library: {ctx_data["library"]["pid"]} '
                f'{error_reason}')
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
        error_reason = ''
        recipients = []
        patron = ctx_data['patron']
        for email in [
            patron.get('email'),
            patron['patron'].get('additional_communication_email')
        ]:
            if email:
                recipients.append(email)
        if not recipients:
            error_reason = '(Missing notification recipients)'
        reply_to = ctx_data['library'].get('email')
        if not reply_to:
            error_reason = '(Missing reply_to email)'
        if error_reason:
            current_app.logger.warning(
                'Notification is lost for patron: '
                f'{ctx_data["patron"]["pid"]} '
                f'send to library: {ctx_data["library"]["pid"]} '
                f'{error_reason}')
            return False
        # delay
        delay_availability = 0
        # get notification settings for notification type
        for setting in ctx_data['library']['notification_settings']:
            if setting['type'] == Notification.AVAILABILITY_NOTIFICATION_TYPE:
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
