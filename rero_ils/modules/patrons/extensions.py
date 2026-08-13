# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron record extensions."""

from flask import current_app, render_template
from flask_mail import Message
from invenio_mail.tasks import send_email
from invenio_records.extensions import RecordExtension

from rero_ils.modules.users.api import User


class UserDataExtension(RecordExtension):
    """Add related user data extension."""

    def pre_dump(self, record, data, dumper=None):
        """Add user data.

        :param record: the record metadata.
        :param data: The dumped data dictionary.
        :param dumper: Dumper to use when dumping the record.
        :return the future dumped data.
        """
        user = User.get_record(record.get("user_id"))
        user_info = user.dumps_metadata()
        return data.update(user_info)


class PatronWelcomeEmailExtension(RecordExtension):
    """Send a welcome email when a patron is created."""

    def post_create(self, record):
        """Build and enqueue the patron welcome email."""
        if not record.is_patron:
            return

        user = record.user
        additional_email = record.patron.get("additional_communication_email")
        recipients = list(dict.fromkeys(address for address in (user.email, additional_email) if address))
        if not recipients:
            return

        organisation = record.organisation
        profile = user.user_profile or {}
        patron_name = " ".join(filter(None, (profile.get("first_name"), profile.get("last_name"))))
        language = record.patron.get(
            "communication_language",
            current_app.config.get("RERO_ILS_DEFAULT_LANGUAGE", "eng"),
        )
        body = render_template(
            f"rero_ils/patrons/email/welcome/{language}.txt",
            patron={
                "name": patron_name or record.formatted_name,
                "additional_email": additional_email,
            },
            organisation={
                "name": organisation.get("name"),
                "address": organisation.get("address"),
                "url": f"{current_app.config.get('RERO_ILS_URL', '').rstrip('/')}/{organisation.get('code')}/",
            },
        )
        subject, _, body = body.partition("\n")
        sender = current_app.config.get("DEFAULT_SENDER_EMAIL", "noreply@rero.ch")
        message = Message(
            subject=subject,
            body=body,
            sender=sender,
            reply_to=sender,
            recipients=recipients,
        )
        send_email.apply_async((message.__dict__,))
