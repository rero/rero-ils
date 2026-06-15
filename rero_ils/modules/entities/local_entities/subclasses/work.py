# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating "work" local entities."""

from ...helpers import str_builder as builder
from ..api import LocalEntity


class WorkLocalEntity(LocalEntity):
    """Work local entity class."""

    def get_authorized_access_point(self, language=None):
        """Get the authorized access point this local entity.

        :return return the calculated authorized access point to use.
        """
        field_builders = [
            builder(self.get("creator"), suffix=". "),
            self.get("title"),
        ]
        return "".join(field_builders)
