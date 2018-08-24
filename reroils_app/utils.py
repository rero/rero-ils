# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities functions for rerpils-app."""

from flask import current_app, render_template
from flask_mail import Message
from flask_security.utils import config_value


def send_mail(subject, recipients, template, language, **context):
    """Send an email via the Flask-Mail extension.

    :param subject: Email subject
    :param recipients: List of email recipients
    :param template: The name of the email template
    :param context: The context to render the template with
    """
    sender = config_value('EMAIL_SENDER')
    msg = Message(subject,
                  sender=sender,
                  recipients=recipients)

    ctx = ('email', template, language)

    if config_value('EMAIL_PLAINTEXT'):
        msg.body = render_template('%s/%s_%s.txt' % ctx, **context)
    # if config_value('EMAIL_HTML'):
    #     msg.html = render_template('%s/%s.html' % ctx, **context)

    mail = current_app.extensions.get('mail')
    mail.send(msg)
