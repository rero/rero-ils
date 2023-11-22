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

"""Entities model class."""


class EntityType:
    """Class holding all available entity types."""

    AGENT = 'bf:Agent'
    ORGANISATION = 'bf:Organisation'
    PERSON = 'bf:Person'
    PLACE = 'bf:Place'
    TEMPORAL = 'bf:Temporal'
    TOPIC = 'bf:Topic'
    WORK = 'bf:Work'


class EntityResourceType:
    """Class holding all available resource entity types."""

    REMOTE = 'remote'
    LOCAL = 'local'


class EntityFieldWithRef:
    """Class to define field with $ref."""

    CONTRIBUTION = 'contribution'
    GENRE_FORM = 'genreForm'
    SUBJECTS = 'subjects'
