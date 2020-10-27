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

from ..locations.api import Location


class Dispatcher:
    """Dispatcher notifications class."""

    def dispatch_notification(self, notification=None, verbose=False):
        """Dispatch the notification."""

        def not_yet_implemented(*args):
            """Do nothing placeholder for a notification."""
            return

        if notification:
            data = notification.replace_pids_and_refs()
            patron = data['loan']['patron']
            communication_switcher = {
                'email': Dispatcher.send_mail,
                #  'sms': not_yet_implemented
                #  'telepathy': self.madness_mind
                #  ...
            }
            dispatcher_function = communication_switcher.get(
                patron['patron']['communication_channel'],
                not_yet_implemented
            )
            if dispatcher_function == not_yet_implemented:
                current_app.logger.warning(
                    'The communication channel of the patron (pid: {pid})'
                    'is not yet implemented'.format(
                        pid=patron['pid']))
            dispatcher_function(data)
            notification = notification.update_process_date()
            if verbose:
                current_app.logger.info(
                    ('Notification: {pid} chanel: {chanel} type:'
                     '{type} loan: {lpid}').format(
                        pid=notification['pid'],
                        chanel=patron['patron']['communication_channel'],
                        type=notification['notification_type'],
                        lpid=data['loan']['pid']
                    )
                )
        return notification

    @staticmethod
    def send_mail(data):
        """Send the notification by email."""
        patron = data['loan']['patron']
        # get the recipient email from loan.patron.patron.email
        recipient = patron.get('email')
        # do nothing if the patron does not have an email
        if not recipient:
            current_app.logger.warning(
                'Patron (pid: {pid}) does not have an email'.format(
                    pid=patron['pid']))
            return
        notification_type = data.get('notification_type')
        language = patron['patron']['communication_language']
        template = 'email/{type}/{lang}.txt'.format(
            type=notification_type,
            lang=language
        )

        # get the sender email from
        # loan.pickup_location_pid.location.library.email
        library = Location.get_record_by_pid(
            data['loan']['pickup_location_pid']).get_library()
        sender = library['email']
        msg = TemplatedMessage(
            template_body=template,
            sender=sender,
            recipients=[recipient],
            ctx=data['loan']
        )
        # additional recipient
        add_recipient = patron['patron'].get('additional_communication_email')
        if add_recipient:
            msg.add_recipient(add_recipient)
        text = msg.body.split('\n')
        msg.subject = text[0]
        msg.body = '\n'.join(text[1:])
        task_send_email.run(msg.__dict__)
