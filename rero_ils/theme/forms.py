# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO ILS forms."""

from flask_security.confirmable import requires_confirmation
from flask_security.forms import Form
from flask_security.forms import LoginForm as BaseLoginForm
from flask_security.utils import get_message, hash_password, verify_and_update_password
from wtforms import StringField, validators

from rero_ils.modules.users.api import User


class LoginForm(BaseLoginForm):
    """The login form (/signin)."""

    # Override EmailField to accept both usernames and emails.
    email = StringField(validators=[validators.DataRequired()])

    def validate(self, extra_validators=None):
        """Validate the form.

        Copied from invenio-flask-security.
        """
        if not super(Form, self).validate(extra_validators=extra_validators):
            return False

        # uses our own manner to retrieve the user, the rest is identical to flask-security
        self.user = None
        user = User.get_by_username_or_email(self.email.data)
        if user:
            self.user = user.user

        if self.user is None:
            self.email.errors.append(get_message("USER_DOES_NOT_EXIST")[0])
            # Reduce timing variation between existing and non-existung users
            hash_password(self.password.data)
            return False
        if not self.user.password:
            self.password.errors.append(get_message("PASSWORD_NOT_SET")[0])
            # Reduce timing variation between existing and non-existung users
            hash_password(self.password.data)
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message("INVALID_PASSWORD")[0])
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message("CONFIRMATION_REQUIRED")[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message("DISABLED_ACCOUNT")[0])
            return False
        return True
