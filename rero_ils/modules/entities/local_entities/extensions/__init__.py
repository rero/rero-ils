# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity record extensions."""

from .authorized_access_point import AuthorizedAccessPointExtension
from .local_entity_factory import LocalEntityFactoryExtension

__all__ = ["AuthorizedAccessPointExtension", "LocalEntityFactoryExtension"]
