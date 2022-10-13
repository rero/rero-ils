# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Permissions for statistics configuration."""

from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByOrganisation, RecordPermissionPolicy

# Actions to control statistics configuration policies for CRUD operations
search_action = action_factory('stat_cfg-search')
read_action = action_factory('stat_cfg-read')
access_action = action_factory('stat_cfg-access')


class StatisticsConfigurationPermissionPolicy(RecordPermissionPolicy):
    """Statistics configuration permission policy for CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
