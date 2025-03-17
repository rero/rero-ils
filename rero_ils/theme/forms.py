# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""RERO ILS forms."""

from flask_security.confirmable import requires_confirmation
from flask_security.forms import Form
from flask_security.forms import LoginForm as BaseLoginForm
from flask_security.utils import get_message, hash_password, verify_and_update_password

from rero_ils.modules.users.api import User


class LoginForm(BaseLoginForm):
    """The login form (/signin)."""

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
