# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import json
from functools import wraps

from flask import Blueprint, abort, current_app, render_template, request
from flask_login import current_user
from invenio_rest import ContentNegotiatedMethodView

from .api import User
from .models import UserRole
from ...modules.patrons.api import Patron, current_librarian
from ...permissions import login_and_librarian


def check_permission(fn):
    """Decorate to check permission access.

    The access is allow when the connected user is a librarian.
    """
    @wraps(fn)
    def is_logged_librarian(*args, **kwargs):
        """Decorated view."""
        login_and_librarian()
        return fn(*args, **kwargs)
    return is_logged_librarian


def check_user_permission(fn):
    """Decorate to check permission access.

    The access is allow when the connected user is a librarian or
    the user id is the same of the id argument.
    """
    @wraps(fn)
    def is_logged(*args, **kwargs):
        """Decorated view."""
        if not current_user.is_authenticated:
            abort(401)
        if not current_librarian and \
                str(current_user.id) != kwargs.get('id', None):
            abort(403)
        return fn(*args, **kwargs)
    return is_logged


def check_user_list_permission(fn):
    """Decorate to check permission access.

    The access is allow when the connected user is a librarian or
    the user id is the same of the id argument.
    """
    @wraps(fn)
    def is_logged(*args, **kwargs):
        """Decorated view."""
        if not current_user.is_authenticated:
            abort(401)
        if not current_librarian and not current_user:
            abort(403)
        return fn(*args, **kwargs)
    return is_logged


def check_user_readonly_permission(fn):
    """Decorate to check permission access.

    The access is allow when the connected user and the profile is not in
    readonly.
    """
    @wraps(fn)
    def is_user_readonly(*args, **kwargs):
        """Decorated view."""
        if current_app.config.get('RERO_PUBLIC_USERPROFILES_READONLY', False) \
                or not current_user.is_authenticated:
            abort(401)
        return fn(*args, **kwargs)
    return is_user_readonly


class UsersResource(ContentNegotiatedMethodView):
    """User REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(
            method_serializers={
                'GET': {
                    'application/json': json.dumps
                },
                'PUT': {
                    'application/json': json.dumps
                }
            },
            serializers_query_aliases={
                'json': json.dumps
            },
            default_method_media_type={
                'GET': 'application/json',
                'PUT': 'application/json'
            },
            default_media_type='application/json',
            **kwargs
        )

    @check_user_permission
    def get(self, id):
        """Implement the GET."""
        user = User.get_record(id)
        return user.dumps()

    @check_user_permission
    def put(self, id):
        """Implement the PUT."""
        user = User.get_record(id)
        user = user.update(request.get_json())
        editing_own_public_profile = str(current_user.id) == id and \
            not (
                current_user.has_role(UserRole.FULL_PERMISSIONS) and
                current_user.has_role(UserRole.USER_MANAGER)
        )
        if editing_own_public_profile:
            Patron.set_communication_channel(user)
        return user.dumps()


class UsersCreateResource(ContentNegotiatedMethodView):
    """User REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(
            method_serializers={
                'GET': {
                    'application/json': json.dumps
                },
                'POST': {
                    'application/json': json.dumps
                }
            },
            serializers_query_aliases={
                'json': json.dumps
            },
            default_method_media_type={
                'GET': 'application/json',
                'POST': 'application/json'
            },
            default_media_type='application/json',
            **kwargs
        )

    @check_user_list_permission
    def get(self):
        """Get user info for the professionnal view."""
        email_or_username = request.args.get('q', '').strip()
        hits = {
            'hits': {
                'hits': [],
                'total': {
                    'relation': 'eq',
                    'value': 0
                }
            }
        }
        if not email_or_username:
            return hits
        if email_or_username.startswith('email:'):
            user = User.get_by_email(
                email_or_username[len('email:'):])
        elif email_or_username.startswith('username:'):
            user = User.get_by_username(
                email_or_username[len('username:'):])
        else:
            user = User.get_by_username_or_email(email_or_username)
        if not user:
            return hits
        # if librarian: send all user data
        # if patron: send only the user id
        data = user.dumps() if current_librarian else {'id': user.id}
        hits['hits']['hits'].append(data)
        hits['hits']['total']['value'] = 1
        return hits

    @check_permission
    def post(self):
        """Implement the POST."""
        user = User.create(request.get_json())
        editing_own_public_profile = str(current_user.id) == user.id and \
            not (
                current_user.has_role(UserRole.FULL_PERMISSIONS) and
                current_user.has_role(UserRole.USER_MANAGER)
        )
        if editing_own_public_profile:
            Patron.set_communication_channel(user)
        return user.dumps()


blueprint = Blueprint(
    'users',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/<string:viewcode>/user/profile')
@check_user_readonly_permission
def profile(viewcode):
    """User Profile editor Page."""
    return render_template('rero_ils/user_profile.html',
                           viewcode=viewcode)


@blueprint.route('/<string:viewcode>/user/password')
@check_user_readonly_permission
def password(viewcode):
    """User change password Page."""
    return render_template('rero_ils/user_password.html',
                           viewcode=viewcode,
                           current_user=current_user)
