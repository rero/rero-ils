# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used to get migrations."""

from flask import Blueprint, jsonify, make_response
from flask import request as flask_request
from invenio_rest import ContentNegotiatedMethodView

from .api import Migration
from .permissions import MigrationPermissionPolicy, check_permission


def _(x):
    """Identity function used to trigger string extraction."""
    return x


def simple_search_json_serializer(data, code=200, headers=None):
    """JSON serializer to reproduce a simple invenio search format."""
    if code != 200:
        return data
    if data:
        hits = [{"metadata": hit["_source"], "id": hit["_id"]} for hit in data["hits"]["hits"]]
        new_data = {"hits": {"hits": hits, "total": data["hits"]["total"]}}
        if data.get("aggregations"):
            new_data["aggregations"] = data["aggregations"]
        res = jsonify(new_data)
    else:
        res = make_response()
    res.status_code = code
    return res


def simple_item_json_serializer(data, code=200, headers=None):
    """JSON serializer to reproduce a simple invenio search format."""
    if code != 200:
        return data
    res = jsonify(data) if data else make_response()
    res.status_code = code
    return res


api_blueprint = Blueprint("api_migrations", __name__, url_prefix="/migrations")


class MigrationsListResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(
            method_serializers={"GET": {"application/json": simple_search_json_serializer}},
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
        query = flask_request.args.get("q")

        search = Migration.search()[(page - 1) * size : page * size].filter(
            MigrationPermissionPolicy("mig-search").query_filters
        )
        if query:
            search = search.query("query_string", query=query)
        search.aggs.bucket(_("status"), "terms", field="status", size=30)
        if status := flask_request.args.get("status"):
            search = search.filter("term", status=status)
        return self.make_response(search.execute().to_dict(), 200)


api_blueprint.add_url_rule("/", view_func=MigrationsListResource.as_view("migrations_list"))
