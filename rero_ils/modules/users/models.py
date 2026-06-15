# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Models for RERO-ILS users."""


class UserRole:
    """Roles available for RERO-ILS users."""

    PATRON = "patron"
    PROFESSIONAL_READ_ONLY = "pro_read_only"
    ACQUISITION_MANAGER = "pro_acquisition_manager"
    FULL_PERMISSIONS = "pro_full_permissions"
    CATALOG_MANAGER = "pro_catalog_manager"
    CIRCULATION_MANAGER = "pro_circulation_manager"
    LIBRARY_ADMINISTRATOR = "pro_library_administrator"
    USER_MANAGER = "pro_user_manager"
    PRO_ENTITY_MANAGER = "pro_entity_manager"
    STATISTICS_MANAGER = "pro_statistic_manager"

    LIBRARIAN_ROLES = [
        PROFESSIONAL_READ_ONLY,
        ACQUISITION_MANAGER,
        CATALOG_MANAGER,
        CIRCULATION_MANAGER,
        LIBRARY_ADMINISTRATOR,
        USER_MANAGER,
        PRO_ENTITY_MANAGER,
        STATISTICS_MANAGER,
    ]

    PROFESSIONAL_ROLES = [FULL_PERMISSIONS, *LIBRARIAN_ROLES]

    ALL_ROLES = [PATRON, *PROFESSIONAL_ROLES]
