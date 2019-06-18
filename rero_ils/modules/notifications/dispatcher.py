# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2019 RERO.
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

"""API for dispatch Notifications."""

from __future__ import absolute_import, print_function

from flask import current_app
from flask_security.utils import config_value
from invenio_mail.api import TemplatedMessage
from invenio_mail.tasks import send_email


class Dispatcher():
    """Dispatcher notifications class."""

    def dispatch_notification(self, notification=None):
        """Dispatch the notification."""
        if notification:
            data = notification.replace_pids_and_refs()
            communication_channel = \
                data['loan']['patron']['communication_channel']
            if communication_channel == 'email':
                self.send_mail(data=data)
            if communication_channel == 'sms':
                pass
            if communication_channel == 'whatsapp':
                pass
            if communication_channel == 'letter':
                pass
            notification = notification.update_process_date()
        return notification

    def send_mail(self, data):
        """Send email."""
        data['loan']['profile_url'] = \
            'https://ils.test.rero.ch/patrons/profile'
        notification_type = data.get('notification_type')
        language = data['loan']['patron']['communication_language']
        template = 'email/{type}/{lang}'.format(
            type=notification_type,
            lang=language
        )
        recipient = data['loan']['patron']['email']
        msg = TemplatedMessage(
            # template_html='{template}.html'.format(template=template),
            template_body='{template}.txt'.format(template=template),
            sender=config_value('EMAIL_SENDER'),
            recipients=[recipient],
            ctx=data['loan']
        )
        text = msg.body.split('\n')
        msg.subject = text[0]
        msg.body = '\n'.join(text[1:])
        try:
            send_email.run(msg.__dict__)
            # TODO: investigate why delay does not work
            # send_email.delay(msg.__dict__)
            # current_app.extensions['mail'].send(msg)
        except Exception as e:
            raise(e)
