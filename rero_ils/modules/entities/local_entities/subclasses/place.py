# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating "place" local entities."""

from ..api import LocalEntity


class PlaceLocalEntity(LocalEntity):
    """Place local entity class."""

    def get_authorized_access_point(self, language=None):
        """Get the authorized access point this local entity.

        :return return the calculated authorized access point to use.
        """
        return self.get("name")
