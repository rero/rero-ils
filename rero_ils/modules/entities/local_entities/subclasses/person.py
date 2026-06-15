# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating "person" local entities."""

from ...helpers import str_builder as builder
from ..api import LocalEntity


class PersonLocalEntity(LocalEntity):
    """Person local entity class."""

    def get_authorized_access_point(self, language=None):
        """Get the authorized access point this local entity.

        :return return the calculated authorized access point to use.
        """
        dates = [self.get("date_of_birth", ""), self.get("date_of_death", "")]
        field_builders = [
            self.get("name"),
            builder(self.get("numeration"), prefix=" "),
            builder(self.get("qualifier"), prefix=", "),
            builder(self.get("fuller_form_of_name"), prefix=" (", suffix=")"),
            builder(dates, delimiter="-", prefix=" (", suffix=")"),
        ]
        return "".join(field_builders)
