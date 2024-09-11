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

import json

from elasticsearch.exceptions import NotFoundError
from flask import Blueprint, abort
from flask import request as flask_request
from invenio_rest import ContentNegotiatedMethodView

from ..permissions import MigrationPermissionPolicy, check_permission

api_blueprint = Blueprint("api_migration_data", __name__, url_prefix="/migration_data")


class MigrationDataListResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        from ..views import simple_search_json_serializer

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
        from ..api import Migration

        migration_id = flask_request.args.get("migration")

        if migration_id:
            try:
                migration = Migration.get(migration_id)
                cls = migration.data_class
                search = cls.search()
            except NotFoundError:
                abort(404)
        else:
            from .api import MigrationData

            search = MigrationData.search(index="migration-data")

        size = int(flask_request.args.get("size", 10))
        size = 0 if size < 0 else size
        page = int(flask_request.args.get("page", 1))
        page = 1 if page < 1 else page
        query = flask_request.args.get("q")
        search = search[(page - 1) * size : page * size].filter(
            MigrationPermissionPolicy("mig-search").query_filters
        )
        search.aggs.bucket("migration", "terms", field="migration_id.raw", size=30)

        search.aggs.bucket(
            "conversion_status", "terms", field="conversion_status", size=30
        )

        if conversion_status := flask_request.args.get("conversion_status"):
            search = search.filter("term", conversion_status=conversion_status)
        if query:
            search = search.query("query_string", query=query)
        return self.make_response(search.execute().to_dict(), 200)


class MigrationDataResource(ContentNegotiatedMethodView):
    """User REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        from ..views import simple_item_json_serializer

        super().__init__(
            method_serializers={
                "GET": {"application/json": simple_item_json_serializer}
            },
            serializers_query_aliases={"json": json.dumps},
            default_method_media_type={"GET": "application/json"},
            default_media_type="application/json",
            **kwargs,
        )

    @check_permission(MigrationPermissionPolicy("read"))
    def get(self, id):
        """Implement the GET."""
        from ..api import Migration

        migration_id = flask_request.args.get("migration")
        if migration_id:
            try:
                migration = Migration.get(migration_id)
                MigrationData = migration.data_class
                migration_data = MigrationData.get(id)
            except NotFoundError:
                abort(404)
        else:
            from .api import MigrationData

            migration_data = next(
                MigrationData.search(index="migration-data")
                .filter("term", _id=id)
                .scan()
            )
            migration = Migration.get(migration_data.migration_id)
        data = migration_data.to_dict()
        data["id"] = migration_data.meta.id
        data["raw"] = migration.conversion_class.markdown(data=migration_data.raw)
        return self.make_response(data, 200)


api_blueprint.add_url_rule(
    "/",
    view_func=MigrationDataListResource.as_view("migration_data_list"),
)

api_blueprint.add_url_rule(
    "<id>",
    view_func=MigrationDataResource.as_view("migration_data_item"),
)
