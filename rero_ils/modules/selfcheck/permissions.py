# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Selfcheck permissions."""

from ...permissions import monitoring_permission
from ..permissions import deny_access


def seflcheck_permission_factory(action):
    """Default api permission factory."""
    return monitoring_permission if action in ["api-monitoring"] else deny_access
