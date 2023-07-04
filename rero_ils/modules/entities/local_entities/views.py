# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Blueprint about local entities."""

from contextlib import suppress
from functools import wraps

from flask import Blueprint, current_app, jsonify, request

from rero_ils.modules.decorators import check_logged_as_librarian
from rero_ils.modules.entities.local_entities.proxy import LocalEntityProxy

api_blueprint = Blueprint('api_local_entities', __name__)


def extract_size_parameter(func):
    """Decorator to extract the size parameter from query string."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'size' not in kwargs:
            kwargs['size'] = current_app.config.get(
                'RERO_ILS_DEFAULT_SUGGESTION_LIMIT')
            with suppress(ValueError):
                kwargs['size'] = int(request.args.get('size') or '')
        return func(*args, **kwargs)
    return wrapper


@api_blueprint.route('/local_entities/search/<term>',
                     defaults={'entity_type': 'agents'})
@api_blueprint.route('/local_entities/search/<entity_type>/<term>')
@api_blueprint.route('/local_entities/search/<entity_type>/<term>/')
@check_logged_as_librarian
@extract_size_parameter
def local_search_proxy(entity_type, term, size):
    """Proxy to search local entities by entity_type.

    :param entity_type: The type of entities to search.
    :param term: the searched term.
    :param size: the number of suggestion to retrieve
    """
    # DEV NOTES :: Why not using invenio list API
    #   In some situation, we need to search on multiple key/filters at same
    #   time. For example, searching for concept[@type=genreForm] requires to
    #   filter query on @type='bf:Topic' and on @genreForm=true.
    #   To not introduce specific logic into external consumers, this endpoint
    #   can analyse the `entity_type` argument to determine the base query to
    #   apply.
    #   See same behavior for remote entities search proxy.

    return jsonify([
        hit.to_dict()
        for hit in LocalEntityProxy(entity_type).search(term, size)
    ])
