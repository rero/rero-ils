# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprints for item."""

from .api_views import api_blueprint
from .rest import InventoryListResource

inventory_list = InventoryListResource.as_view("inventory_search")
api_blueprint.add_url_rule("/inventory", view_func=inventory_list)

blueprints = [
    api_blueprint,
]

__all__ = "api_blueprint"
