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

"""Password validator."""

from wtforms import ValidationError

from rero_ils.modules.utils import PasswordValidatorException, \
    password_validator


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
            password_validator(field.data, length=self.length,
                               special_char=self.special_char)
        except PasswordValidatorException as e:
            raise ValidationError(str(e)) from e
