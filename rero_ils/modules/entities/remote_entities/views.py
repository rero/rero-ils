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

"""Blueprint about remote entities."""

from __future__ import absolute_import, print_function

from flask import Blueprint, abort

from rero_ils.modules.decorators import check_logged_as_librarian

from .proxy import MEFProxyFactory

api_blueprint = Blueprint(
    'api_remote_entities',
    __name__
)


@api_blueprint.route('/remote_entities/search/<term>',
                     defaults={'entity_type': 'agents'})
@api_blueprint.route('/remote_entities/search/<entity_type>/<term>')
@api_blueprint.route('/remote_entities/search/<entity_type>/<term>/')
@check_logged_as_librarian
def remote_search_proxy(entity_type, term):
    """Proxy to search entities on remote server.

    Currently, we only search on MEF remote servers. If multiple remote sources
    are possible to search, a request must be sent to each remote API and
    all result must be unified into a common response.

    :param entity_type: The type of entities to search.
    :param term: the searched term.
    """
    try:
        return MEFProxyFactory.create_proxy(entity_type).search(term)
    except ValueError as err:
        abort(400, str(err))
