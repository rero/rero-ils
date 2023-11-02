# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Models for RERO-ILS users."""


class UserRole:
    """Roles available for RERO-ILS users."""

    PATRON = 'patron'
    PROFESSIONAL_READ_ONLY = 'pro_read_only'
    ACQUISITION_MANAGER = 'pro_acquisition_manager'
    FULL_PERMISSIONS = 'pro_full_permissions'
    CATALOG_MANAGER = 'pro_catalog_manager'
    CIRCULATION_MANAGER = 'pro_circulation_manager'
    LIBRARY_ADMINISTRATOR = 'pro_library_administrator'
    USER_MANAGER = 'pro_user_manager'
    PRO_ENTITY_MANAGER = 'pro_entity_manager'
    STATISTICS_MANAGER = 'pro_statistic_manager'

    LIBRARIAN_ROLES = [
        PROFESSIONAL_READ_ONLY, ACQUISITION_MANAGER,
        CATALOG_MANAGER, CIRCULATION_MANAGER,
        LIBRARY_ADMINISTRATOR, USER_MANAGER, PRO_ENTITY_MANAGER,
        STATISTICS_MANAGER
    ]

    PROFESSIONAL_ROLES = [FULL_PERMISSIONS] + LIBRARIAN_ROLES

    ALL_ROLES = [PATRON] + PROFESSIONAL_ROLES
