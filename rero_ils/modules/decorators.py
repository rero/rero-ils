# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Shared module decorators."""

from functools import wraps

from flask import abort, jsonify, redirect
from flask_login import current_user
from werkzeug.exceptions import HTTPException

from rero_ils.permissions import librarian_permission, login_and_librarian, \
    login_and_patron


def check_authentication(fn):
    """Decorator to check authentication for permissions HTTP API."""
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        if not librarian_permission.require().can():
            return jsonify({'status': 'error: Forbidden'}), 403
        return fn(*args, **kwargs)

    return decorated_view


def check_logged_as_librarian(fn):
    """Decorator to check if the current logged user is logged as librarian.

    If no user is connected: return 401 (unauthorized)
    If current logged user isn't `librarian`: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        login_and_librarian()
        return fn(*args, **kwargs)
    return wrapper


def check_logged_as_patron(fn):
    """Decorator to check if the current logged user is logged as patron.

    If no user is connected: redirect the user to sign-in page
    If current logged user isn't `patron`: return 403 (forbidden)
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        status, code, redirect_url = login_and_patron()
        if status:
            return fn(*args, **kwargs)
        elif redirect_url:
            return redirect(redirect_url)
        else:
            abort(code)
    return wrapper


def check_logged_user_authentication(func):
    """Decorator to check authentication for user HTTP API."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'status': 'error: Unauthorized'}), 401
        return func(*args, **kwargs)

    return decorated_view


def jsonify_error(func):
    """Jsonify errors."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException as httpe:
            return jsonify({'message': f'{httpe}'}), httpe.code
        except Exception as error:
            # raise error
            # current_app.logger.error(str(error))
            return jsonify({'message': f'{error}'}), 400
    return decorated_view
