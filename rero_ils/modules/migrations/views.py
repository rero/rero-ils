# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Blueprint used to get migrations."""
from functools import wraps

from flask import Blueprint, abort, jsonify, make_response
from flask import request as flask_request
from flask_login import current_user
from invenio_rest import ContentNegotiatedMethodView

from .api import Migration
from .permissions import MigrationPermissionPolicy


def check_permission(permission):
    """Decorator to check if current connected user has access to an action.

    :param actions: List of `ActionNeed` to test. If one permission failed
        then the access should be unauthorized.
    """

    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(make_response(jsonify({"status": "error: Unauthorized"}), 401))
            if not permission.can():
                abort(make_response(jsonify({"status": "error: Forbidden"}), 403))
            return func(*args, **kwargs)

        return wrapper

    return inner


def simple_search_json_serializer(data, code=200, headers=None):
    """JSON serializer to reproduce a simple invenio search format."""
    if code != 200:
        return data
    if data:
        hits = [
            dict(metadata=hit["_source"], id=hit["_id"]) for hit in data["hits"]["hits"]
        ]
        new_data = dict(hits=dict(hits=hits, total=data["hits"]["total"]))
        res = jsonify(new_data)
    else:
        res = make_response()
    res.status_code = code
    return res


api_blueprint = Blueprint("api_migrations", __name__, url_prefix="/migrations")


class MigrationsListResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(
            method_serializers={
                "GET": {"application/json": simple_search_json_serializer}
            },
            serializers_query_aliases={"json": "application/json"},
            default_method_media_type={"GET": "application/json"},
            default_media_type="application/json",
            **kwargs,
        )

    @check_permission(MigrationPermissionPolicy("search"))
    def get(self, **kwargs):
        """HTTP GET method."""
        size = int(flask_request.args.get("size", 10))
        size = 0 if size < 0 else size
        page = int(flask_request.args.get("page", 1))
        page = 1 if page < 1 else page
        search = Migration.search()[(page - 1) * size : size].filter(
            MigrationPermissionPolicy("mig-search").query_filters
        )
        return self.make_response(search.execute().to_dict(), 200)


api_blueprint.add_url_rule(
    "/", view_func=MigrationsListResource.as_view("migrations_list")
)
