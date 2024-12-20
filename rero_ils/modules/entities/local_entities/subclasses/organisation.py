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
