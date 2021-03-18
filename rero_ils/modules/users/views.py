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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

import json
from functools import wraps

from flask import request
from invenio_rest import ContentNegotiatedMethodView

from .api import User
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

    @check_permission
    def get(self, id):
        """Implement the GET."""
        user = User.get_by_id(id)
        return user.dumps()

    @check_permission
    def put(self, id):
        """Implement the PUT."""
        user = User.get_by_id(id)
        user = user.update(request.get_json())
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

    @check_permission
    def get(self):
        """Get user info for the professionnal view."""
        email_or_username = request.args.get('q', None).strip()
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
        data = user.dumps()
        hits['hits']['hits'].append(data)
        hits['hits']['total']['value'] = 1
        return hits

    @check_permission
    def post(self):
        """Implement the POST."""
        user = User.create(request.get_json())
        return user.dumps()
