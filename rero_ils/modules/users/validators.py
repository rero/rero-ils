# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Password validator."""

from wtforms import ValidationError

from rero_ils.modules.utils import PasswordValidatorException, password_validator


class PasswordValidator:
    """Password Validator."""

    def __init__(self, length=8, special_char=False):
        """Password validator class initializer."""
        self.length = length
        self.special_char = special_char

    def __call__(self, form, field):
        """Call.

        :param form: the current form.
        :param field: the password field.
        :raise ValidationError: If the password is invalid.
        """
        try:
            password_validator(field.data, length=self.length, special_char=self.special_char)
        except PasswordValidatorException as e:
            raise ValidationError(str(e)) from e
