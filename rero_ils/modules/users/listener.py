# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Listener user auth forms."""

from .forms import RegisterForm, ResetPasswordForm


def user_register_forms(sender, app=None, **kwargs):
    """Register form (personalized).

    :param sender: the application factory function.
    :param app: the Flask application instance.
    :param kwargs: additional arguments.
    """
    if security := app.extensions.get("security"):
        # Override Register form
        security.register_form = RegisterForm


def user_reset_password_forms(sender, app=None, **kwargs):
    """Change password form (personalized).

    :param sender: the application factory function.
    :param app: the Flask application instance.
    :param kwargs: additional arguments.
    """
    if security := app.extensions.get("security"):
        # Override Reset password form
        security.reset_password_form = ResetPasswordForm
