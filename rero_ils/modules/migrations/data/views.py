# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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
from datetime import datetime, timezone

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Index
from flask import Blueprint, abort
from flask import request as flask_request
from invenio_rest import ContentNegotiatedMethodView

from rero_ils.modules.documents.dumpers.indexer import IndexerDumper
from rero_ils.modules.documents.extensions import (
    EditionStatementExtension,
    ProvisionActivitiesExtension,
    SeriesStatementExtension,
    TitleExtension,
)
from rero_ils.modules.patrons.api import current_librarian

from ..permissions import MigrationPermissionPolicy, check_permission

api_blueprint = Blueprint("api_migration_data", __name__, url_prefix="/migration_data")


def _(x):
    """Identity function used to trigger string extraction."""
    return x


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

    def process_hit(self, hit):
        """Add information to the given search hit."""
        data = hit["_source"].get("conversion", {}).get("json")
        if not data:
            return hit
        TitleExtension().post_dump({}, data)
        IndexerDumper._process_provision_activity(data, data)
        ProvisionActivitiesExtension().post_dump({}, data)
        EditionStatementExtension().post_dump({}, data)
        SeriesStatementExtension().post_dump({}, data)
        return hit

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

        # get request args
        size = int(flask_request.args.get("size", 10))
        size = 0 if size < 0 else size
        page = int(flask_request.args.get("page", 1))
        page = 1 if page < 1 else page
        query = flask_request.args.get("q")

        # base query and filter by organization
        search = search[(page - 1) * size : page * size].filter(
            MigrationPermissionPolicy("mig-search").query_filters
        )

        # aggregations
        search.aggs.bucket(_("migration"), "terms", field="migration_id.raw", size=30)
        search.aggs.bucket(_("batch"), "terms", field="deduplication.subset", size=30)
        search.aggs.bucket(
            _("conversion_status"), "terms", field="conversion.status", size=30
        )
        search.aggs.bucket(
            _("deduplication_status"), "terms", field="deduplication.status", size=30
        )
        search.aggs.bucket(
            _("modified_by"), "terms", field="deduplication.modified_by.raw", size=30
        )

        # filters
        if conversion_status := flask_request.args.get("conversion_status"):
            search = search.filter("term", conversion__status=conversion_status)
        if batch := flask_request.args.get("batch"):
            search = search.filter("term", deduplication__subset=batch)
        if deduplication_status := flask_request.args.get("deduplication_status"):
            search = search.filter("term", deduplication__status=deduplication_status)
        if modified_by := flask_request.args.get("modified_by"):
            search = search.filter("term", deduplication__modified_by__raw=modified_by)
        # sorting
        if sort_by := flask_request.args.get("sort"):
            search = search.sort(sort_by)
        # user query
        if query:
            search = search.query("query_string", query=query)

        results = search.execute().to_dict()
        hits = results.get("hits", {}).get("hits", [])
        results["hits"]["hits"] = [self.process_hit(hit) for hit in hits]
        return self.make_response(results, 200)


class MigrationDataResource(ContentNegotiatedMethodView):
    """User REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        from ..views import simple_item_json_serializer

        super().__init__(
            method_serializers={
                "GET": {"application/json": simple_item_json_serializer},
                "PUT": {"application/json": simple_item_json_serializer},
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

    @check_permission(MigrationPermissionPolicy("update"))
    def put(self, id):
        """Implement the PUT."""
        from ..api import Migration

        migration_id = flask_request.args.get("migration")
        body = flask_request.get_json()
        if not body or "ils_pid" not in body:
            abort(400)
        ils_pid = body["ils_pid"]

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
        migration_data.deduplication.ils_pid = ils_pid
        if not ils_pid:
            migration_data.deduplication.status = "no match"
        else:
            migration_data.deduplication.status = "match"
        if candidates := body.get("candidates"):
            migration_data.deduplication.candidates = candidates
        if current_librarian:
            migration_data.deduplication.modified_by = current_librarian.formatted_name
        migration_data.deduplication.modified_at = datetime.now(timezone.utc)
        migration_data.save()
        Index(name=migration.data_index_name).refresh()

        data = migration_data.to_dict()
        data["id"] = migration_data.meta.id
        data["raw"] = migration.conversion_class.markdown(data=migration_data.raw)
        return self.make_response(data, 201)


api_blueprint.add_url_rule(
    "/",
    view_func=MigrationDataListResource.as_view("migration_data_list"),
)

api_blueprint.add_url_rule(
    "<id>",
    view_func=MigrationDataResource.as_view("migration_data_item"),
)
