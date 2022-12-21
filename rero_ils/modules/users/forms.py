# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""User forms."""

from flask import current_app
from flask_security.forms import RegisterForm as SecurityRegisterForm
from flask_security.forms import ResetPasswordForm as SecurityResetPasswordForm
from flask_security.forms import password_required

from .validators import PasswordValidator


class RegisterForm(SecurityRegisterForm):
    """Register form."""

    def __init__(self, *args, **kwargs):
        """Register form class initializer."""
        super().__init__(*args, **kwargs)
        self.password.validators = [
            password_required,
            PasswordValidator(
                length=current_app.config['RERO_ILS_PASSWORD_MIN_LENGTH'],
                special_char=current_app.config[
                    'RERO_ILS_PASSWORD_SPECIAL_CHAR'])
        ]


class ResetPasswordForm(SecurityResetPasswordForm):
    """Change password form."""

    def __init__(self, *args, **kwargs):
        """Reset password form class initializer."""
        super().__init__(*args, **kwargs)
        self.password.validators = [
            password_required,
            PasswordValidator(
                length=current_app.config['RERO_ILS_PASSWORD_MIN_LENGTH'],
                special_char=current_app.config[
                    'RERO_ILS_PASSWORD_SPECIAL_CHAR'])
        ]
