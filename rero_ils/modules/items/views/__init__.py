# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprints for item."""

from .api_views import api_blueprint

blueprints = [
    api_blueprint,
]

__all__ = ("api_blueprint",)
