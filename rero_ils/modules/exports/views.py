# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""RERO ILS exports views."""
from copy import deepcopy
from functools import partial

from flask import Blueprint
from invenio_pidstore import current_pidstore
from invenio_records_rest.query import es_search_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import need_record_permission
from invenio_rest import ContentNegotiatedMethodView
from invenio_search import RecordsSearch


def create_blueprint_from_app(app):
    """Create RERO exports blueprint from a Flask application.

    .. note::
        This function assumes that the application has loaded all extensions
        that want to register REST endpoints via the ``RECORDS_REST_ENDPOINTS``
        configuration variable.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    api_blueprint = Blueprint('api_exports', __name__, url_prefix='')
    endpoints = app.config.get('RERO_EXPORT_REST_ENDPOINTS', {})
    for key, config in endpoints.items():
        copy_config = deepcopy(config)
        resource_config = copy_config.pop('resource', {})
        route_config = resource_config | copy_config  # merging dictionary
        rule = create_export_url_route(key, **route_config)
        api_blueprint.add_url_rule(**rule)
    return api_blueprint


def create_export_url_route(endpoint, default_media_type=None,
                            list_permission_factory_imp=None,
                            list_route=None, pid_fetcher=None,
                            search_class=None,
                            search_factory_imp=None,
                            search_serializers=None,
                            search_serializers_aliases=None, **kwargs):
    """Create Werkzeug URL rule for resource streamed export.

    :param kwargs: all argument necessary to build the flask endpoint.
    :returns: a configuration dict who can be passed as keywords argument to
        ``Blueprint.add_url_rule``.
    """
    assert list_route
    assert search_serializers

    # BUILD LIST_ROUTE AND VIEW_NAME
    #   Override the resource `list_route` adding an "export" prefix.
    #   NOTE: Using REST guidelines it should be best to build the path using
    #     "export" as url suffix ; but it can't be done here because this url
    #     is already used for record serialization.
    view_name = f'{endpoint}_export'
    list_route = f'/export{list_route}'

    # ACCESS PERMISSIONS
    #   Permission to access to any export route are the same as list resource
    #   records permission.
    permission_factory = obj_or_import_string(list_permission_factory_imp)

    search_class = obj_or_import_string(search_class, default=RecordsSearch)

    export_view = ExportResource.as_view(
        view_name,
        default_media_type=default_media_type,
        permission_factory=permission_factory,
        pid_fetcher=pid_fetcher,
        search_class=search_class,
        search_serializers=search_serializers,
        serializers_query_aliases=search_serializers_aliases,
        search_factory=obj_or_import_string(
            search_factory_imp, default=es_search_factory)
    )
    return {'rule': list_route, 'view_func': export_view}


class ExportResource(ContentNegotiatedMethodView):
    """Resource for records streamed exports."""

    def __init__(self, default_media_type=None, permission_factory=None,
                 pid_fetcher=None, search_class=None, search_factory=None,
                 search_serializers=None, serializers_query_aliases=None,
                 **kwargs):
        """Init magic method."""
        serializers = {
            mime: obj_or_import_string(search_obj)
            for mime, search_obj in search_serializers.items() or {}.items()
        }
        super().__init__(
            method_serializers={'GET': serializers},
            serializers_query_aliases=serializers_query_aliases,
            default_method_media_type={'GET': default_media_type},
            default_media_type=default_media_type,
            **kwargs
        )
        self.permission_factory = permission_factory
        self.pid_fetcher = current_pidstore.fetchers[pid_fetcher]
        self.search_class = search_class
        self.search_factory = partial(search_factory, self)

    @need_record_permission('permission_factory')
    def get(self, **kwargs):
        """Implements GET /export/{resource_list_name}."""
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)
        search, _ = self.search_factory(search)

        return self.make_response(
            pid_fetcher=None,
            search_result=search.scan()
        )
