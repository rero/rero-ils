# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
                length=current_app.config["RERO_ILS_PASSWORD_MIN_LENGTH"],
                special_char=current_app.config["RERO_ILS_PASSWORD_SPECIAL_CHAR"],
            ),
        ]


class ResetPasswordForm(SecurityResetPasswordForm):
    """Change password form."""

    def __init__(self, *args, **kwargs):
        """Reset password form class initializer."""
        super().__init__(*args, **kwargs)
        self.password.validators = [
            password_required,
            PasswordValidator(
                length=current_app.config["RERO_ILS_PASSWORD_MIN_LENGTH"],
                special_char=current_app.config["RERO_ILS_PASSWORD_SPECIAL_CHAR"],
            ),
        ]
