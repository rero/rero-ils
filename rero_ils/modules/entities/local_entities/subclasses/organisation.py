# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating "organisation" local entities."""

from ...helpers import str_builder as builder
from ..api import LocalEntity


class OrganisationLocalEntity(LocalEntity):
    """Person local entity class."""

    def get_authorized_access_point(self, language=None):
        """Get the authorized access point this local entity.

        :return return the calculated authorized access point to use.
        """
        conference = [
            self.get("conference_numbering", ""),
            self.get("conference_date", ""),
            self.get("conference_place", ""),
        ]
        field_builders = [
            self.get("name"),
            builder(self.get("subordinate_units"), prefix=". ", delimiter=". "),
            builder(conference, delimiter=" ; ", prefix=" (", suffix=")"),
        ]
        return "".join(field_builders)
