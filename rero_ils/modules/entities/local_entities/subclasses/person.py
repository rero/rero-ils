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

"""API for manipulating "person" local entities."""

from ..api import LocalEntity
from ...helpers import str_builder as builder


class PersonLocalEntity(LocalEntity):
    """Person local entity class."""

    def get_authorized_access_point(self, language=None):
        """Get the authorized access point this local entity.

        :return return the calculated authorized access point to use.
        """
        dates = [self.get('date_of_birth', ''), self.get('date_of_death', '')]
        field_builders = [
            self.get('name'),
            builder(self.get('numeration'), prefix=' '),
            builder(self.get('qualifier'), prefix=', '),
            builder(self.get('fuller_form_of_name'), prefix=' (', suffix=')'),
            builder(dates, delimiter='-', prefix=' (', suffix=')')
        ]
        return ''.join(field_builders)
