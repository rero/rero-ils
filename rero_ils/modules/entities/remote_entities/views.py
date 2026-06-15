# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint about remote entities."""

from flask import Blueprint, abort

from rero_ils.modules.decorators import check_logged_as_librarian

from .proxy import MEFProxyFactory

api_blueprint = Blueprint("api_remote_entities", __name__)


@api_blueprint.route("/remote_entities/search/<term>", defaults={"entity_type": "agents"})
@api_blueprint.route("/remote_entities/search/<entity_type>/<term>")
@api_blueprint.route("/remote_entities/search/<entity_type>/<term>/")
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
