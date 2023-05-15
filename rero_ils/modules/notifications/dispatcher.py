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

"""API for dispatch Notifications."""

from __future__ import absolute_import, print_function

from flask import current_app
from invenio_mail.api import TemplatedMessage
from invenio_mail.tasks import send_email as task_send_email

from .api import Notification
from .models import NotificationType, RecipientType


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
            """Find the dispatcher function to use by communication channel."""
            try:
                communication_switcher = current_app.config.get(
                    'RERO_ILS_COMMUNICATION_DISPATCHER_FUNCTIONS', [])
                return communication_switcher[channel]
            except KeyError:
                current_app.logger.warning(
                    f'The communication channel: {channel}'
                    ' is not yet implemented')
                return Dispatcher.not_yet_implemented

        sent = not_sent = errors = 0
        aggregated = {}
        pids = notification_pids or []
        notifications = [Notification.get_record_by_pid(pid) for pid in pids]
        notifications = list(filter(None, notifications))

        # PROCESS NOTIFICATIONS
        #   For each notification to process, we try to determine if this
        #   notification could be cancelled and/or resent. If yes, append the
        #   notification to the aggregation dict
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
        #   The aggregation key we build ensure than aggregated notifications
        #   are always send to same recipient (patron, lib, vendor, ...) with
        #   the same communication channel. So we can check any notification
        #   of the set to get the these informations.
        for aggr_key, aggr_notifications in aggregated.items():
            notification = aggr_notifications[0]
            comm_channel = notification.get_communication_channel()
            dispatcher_function = get_dispatcher_function(comm_channel)
            counter = len(aggr_notifications)
            if verbose:
                msg = f'Dispatch notifications: {notification.type} '
                if hasattr(notification, 'library'):
                    msg += f'library: {notification.library.pid} '
                if hasattr(notification, 'patron'):
                    msg += f'patron: {notification.patron.pid} '
                msg += f'documents: {counter}'
                current_app.logger.info(msg)
            result, recipients = dispatcher_function(aggr_notifications)
            for notification in aggr_notifications:
                notification.update_process_date(sent=result)
            if result:
                sent += counter
                for notification in aggr_notifications:
                    notification.update_effective_recipients(recipients)
            else:
                not_sent += counter
        return {
            'processed': len(notifications),
            'sent': sent,
            'not_sent': not_sent,
            'errors': errors
        }

    @classmethod
    def _process_notification(cls, notification, resend, aggregated):
        """Process one notification.

        :param notification: the notification to process.
        :param resend: is the notification should be resend notification
                       if already send.
        :param aggregated: ``dict`` to store notification results.
        """
        # 1. Check if notification has already been processed and if we
        #    need to resend it. If not, skip this notification and continue
        process_date = notification.get('process_date')
        if process_date:
            current_app.logger.warning(
                f'Notification: {notification.pid} already processed '
                f'on: {process_date}'
            )
            if not resend:
                return

        # 2. Check if we really need to process the notifications in the case
        #    of asynchronous notifications. If not, then update the
        #    notification 'status' and stop the notification processing.
        can_cancel, reason = notification.can_be_cancelled()
        if can_cancel:
            msg = f'Notification #{notification.pid} cancelled: {reason}'
            current_app.logger.info(msg)
            notification.update_process_date(sent=False, status='cancelled')
            return

        # 3. Aggregate notifications
        aggr_key = notification.aggregation_key
        aggregated.setdefault(aggr_key, [])
        aggregated[aggr_key].append(notification)

    @staticmethod
    def _create_email(recipients, reply_to, ctx_data, template,
                      cc=None, bcc=None):
        """Create email message from template.

        :param recipients: Main recipient emails list
        :param reply_to: Reply to email address.
        :param cc: Email list where to send the message as "copy"
        :param bcc: Email list where to send the message as "blind copy"
        :param ctx_data: Dictionary with information used in template.
        :param template: Template to use to create TemplatedMessage.
        :returns: Message created.
        """
        msg = TemplatedMessage(
            template_body=template,
            sender=current_app.config.get('DEFAULT_SENDER_EMAIL',
                                          'noreply@rero.ch'),
            reply_to=','.join(reply_to),  # the client is unable to manage list
            recipients=recipients,
            cc=cc,
            bcc=bcc,
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
    def send_mail_for_printing(notifications=None):
        """Send a set of notification by mail.

         A this time, we doesn't have any way to send a notification using
         classic mail (postal) process. The solution is to send an email
         to the library address. The library will print this email and send it
         to the correct recipient.

         TODO : Implement a way to send notifications to a async PDF’s
                generator process working with CUPS (using RabbitMQ queue)

        :param notifications: the notification set to perform.
        :return a tuple where first element is a boolean value to determine if
            email was sent (False if errors are found) ; second element is a
            list of used recipients.
        :rtype tuple
        """
        notifications = notifications or []
        if not notifications:
            return True

        notification = notifications[0]
        # 1. Find the library were to send the message.
        #   - for AVAILABILITY, we need to use the pickup library
        #   - for BOOKING and TRANSIT, we need to use the transaction library
        #   - for other notifications, we need to use library
        library = notification.library
        if notification.type in [
            NotificationType.BOOKING,
            NotificationType.TRANSIT_NOTICE
        ]:
            library = notification.transaction_library
        elif notification.type == NotificationType.AVAILABILITY:
            library = notification.pickup_library
        recipient = library.get_email(notification.type)

        # 2. For a REQUEST notification we mainly need to use the email define
        #    on the location. If the location email isn't defined, then use the
        #    library email by default.
        if notification.type == NotificationType.REQUEST:
            recipient = notification.location.get(
                'notification_email', recipient)

        error_reasons = []
        reply_to = notification.library.get('email')
        if not recipient:
            error_reasons.append('Missing notification email')
        if not reply_to:
            error_reasons.append('Missing notification reply_to email')
        if error_reasons:
            current_app.logger.warning(
                f'Notification#{notification.pid} for printing is lost :: '
                f'({")(".join(error_reasons)})')
            return False, None

        # 2. Build the context to render the template
        notif_class = notification.__class__
        context = notif_class.get_notification_context(notifications)
        # 3. Force patron communication channel to 'mail'
        #    In some cases we force the notification to be sent by mail despite
        #    the patron asked to receive them by email (cipo reminders
        #    notifications with a communication channel to 'mail' value).
        #    Ensure than the ``include_patron_address`` are set to True.
        context['include_patron_address'] = True

        # 3. Send the message
        msg = Dispatcher._create_email(
            recipients=[recipient],
            reply_to=[reply_to],
            ctx_data=context,
            template=notification.get_template_path()
        )
        task_send_email.apply_async((msg.__dict__,))
        return True, [(RecipientType.TO, recipient)]

    @staticmethod
    def send_notification_by_email(notifications):
        """Send the notification by email to the patron.

        :param notifications: the notification set to perform.
        :return a tuple where first element is a boolean value to determine if
            email was sent (False if errors are found) ; second element is a
            list of used recipients.
        :rtype tuple
        """
        notifications = notifications or []
        if not notifications:
            return True

        notification = notifications[0]
        reply_to = notification.get_recipients(RecipientType.REPLY_TO)
        recipients = notification.get_recipients(RecipientType.TO)
        cc = notification.get_recipients(RecipientType.CC)
        bcc = notification.get_recipients(RecipientType.BCC)

        error_reasons = []
        if not recipients:
            error_reasons.append('Missing notification recipients')
        if not reply_to:
            error_reasons.append('Missing reply_to email')
        if error_reasons:
            current_app.logger.warning(
                f'Notification#{notification.pid} is lost :: '
                f'({")(".join(error_reasons)})')
            return False, None

        # build the context for this notification set
        notif_class = notification.__class__
        context = notif_class.get_notification_context(notifications)

        msg = Dispatcher._create_email(
            recipients=recipients,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            ctx_data=context,
            template=notification.get_template_path()
        )
        delay = context.get('delay', 0)
        task_send_email.apply_async((msg.__dict__,), countdown=delay)
        return True, [(RecipientType.TO, addr) for addr in recipients]
