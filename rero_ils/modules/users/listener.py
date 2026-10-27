# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Listener user auth forms."""

from functools import wraps

from flask import flash, redirect
from flask_babel import gettext as _
from flask_security.recoverable import reset_password_token_status
from flask_security.utils import url_for_security

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


def user_reset_password_view(sender, app=None, **kwargs):
    """Stop the reset password view from mailing a user without email.

    An expired token makes Flask-Security send new instructions, and a reset
    sends a notice: both fail when the user's email has been removed since.

    :param sender: the application factory function.
    :param app: the Flask application instance.
    :param kwargs: additional arguments.
    """
    endpoint = "security.reset_password"
    if not (view := app.view_functions.get(endpoint)):
        return

    @wraps(view)
    def reset_password(token):
        _expired, _invalid, user = reset_password_token_status(token)
        if user and not user.email:
            flash(_("Your account has no email address. Please contact your library to reset your password."), "error")
            return redirect(url_for_security("forgot_password"))
        return view(token)

    app.view_functions[endpoint] = reset_password
