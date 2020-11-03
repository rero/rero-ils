# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Invenio Account custom views."""

from flask import after_this_request, current_app
from flask import request as flask_request
from invenio_accounts.utils import change_user_password
from invenio_accounts.views.rest import \
    ChangePasswordView as BaseChangePasswordView
from invenio_accounts.views.rest import LoginView as CoreLoginView
from invenio_accounts.views.rest import _commit, use_args, use_kwargs
from invenio_userprofiles.models import UserProfile
from marshmallow import Schema, fields
from sqlalchemy.orm.exc import NoResultFound
from webargs import ValidationError, fields, validate
from werkzeug.local import LocalProxy

from .modules.patrons.api import Patron, current_patron
from .modules.patrons.permissions import PatronPermission

current_datastore = LocalProxy(
    lambda: current_app.extensions['security'].datastore)


#
# Field validators
#
def user_exists(email):
    """Validate that a user exists."""
    try:
        profile = UserProfile.get_by_username(email)
    except NoResultFound:
        if not current_datastore.get_user(email):
            raise ValidationError('USER_DOES_NOT_EXIST')


class LoginView(CoreLoginView):
    """invenio-accounts Login REST View."""

    post_args = {
        'email': fields.String(required=True, validate=[user_exists]),
        'password': fields.String(required=True)
    }

    def get_user(self, email=None, **kwargs):
        """Retrieve a user by the provided arguments."""
        try:
            profile = UserProfile.get_by_username(email)
            return profile.user
        except NoResultFound:
            pass
        return current_datastore.get_user(email)

    @use_kwargs(post_args)
    def post(self, **kwargs):
        """Verify and login a user."""
        user = self.get_user(**kwargs)
        self.verify_login(user, **kwargs)
        self.login_user(user)
        return self.success_response(user)


class PasswordPassword(Schema):
    """Args validation when a user want to change his password."""

    password = fields.String(
        validate=[validate.Length(min=6, max=128)])
    new_password = fields.String(
        required=True, validate=[validate.Length(min=6, max=128)])


class UsernamePassword(Schema):
    """Args validation when a professional change a password for a user."""

    username = fields.String(
        validate=[validate.Length(min=1, max=128)])
    new_password = fields.String(
        required=True, validate=[validate.Length(min=6, max=128)])


def make_password_schema(request):
    """Select the right args validation depending on the context."""
    # Filter based on 'fields' query parameter
    fields = request.args.get('fields', None)
    only = fields.split(',') if fields else None
    # Respect partial updates for PATCH requests
    partial = request.method == 'PATCH'
    if request.json.get('username'):
        return UsernamePassword(only=only,
                                partial=partial, context={"request": request})

    # Add current request to the schema's context
    return PasswordPassword(only=only,
                            partial=partial, context={"request": request})


class ChangePasswordView(BaseChangePasswordView):
    """View to change the user password."""

    def verify_permission(self, username, **args):
        """Check permissions.

        Check if the current user can change a password for an other user.
        """
        patron = Patron.get_patron_by_username(username)
        if not PatronPermission.can_create(current_patron, patron, patron):
            return current_app.login_manager.unauthorized()

    def change_password_for_user(self, username, new_password, **kwargs):
        """Perform change password for a specific user."""
        after_this_request(_commit)
        patron = Patron.get_patron_by_username(username)
        change_user_password(user=patron.user,
                             password=new_password)

    @use_args(make_password_schema)
    def post(self, args):
        """Change user password."""
        if flask_request.json.get('username'):
            self.verify_permission(**args)
            self.change_password_for_user(**args)
        else:
            self.verify_password(**args)
            self.change_password(**args)
        return self.success_response()
