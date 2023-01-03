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

"""Listener user auth forms."""

from .forms import RegisterForm, ResetPasswordForm


def user_register_forms(sender, app=None, **kwargs):
    """Register form (personalized).

    :param sender: the application factory function.
    :param app: the Flask application instance.
    :param kwargs: additional arguments.
    """
    if security := app.extensions.get('security'):
        # Override Register form
        security.register_form = RegisterForm


def user_reset_password_forms(sender, app=None, **kwargs):
    """Change password form (personalized).

    :param sender: the application factory function.
    :param app: the Flask application instance.
    :param kwargs: additional arguments.
    """
    if security := app.extensions.get('security'):
        # Override Reset password form
        security.reset_password_form = ResetPasswordForm
