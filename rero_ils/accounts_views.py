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

from invenio_accounts.views.rest import LoginView as CoreLoginView
from invenio_accounts.views.rest import use_kwargs
from invenio_userprofiles.models import UserProfile
from sqlalchemy.orm.exc import NoResultFound
from webargs import ValidationError, fields
from werkzeug.local import LocalProxy

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
