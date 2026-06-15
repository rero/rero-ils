# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Api harvester errors."""


class ApiHarvesterError(Exception):
    """Base exception for API harvester."""


class ApiRequestError(ApiHarvesterError):
    """Error with the Api request."""


class NameOrUrlMissing(ApiHarvesterError):
    """Name or url for harvesting missing."""


class WrongDateCombination(ApiHarvesterError):
    """'Until' date is larger that 'from' date."""


class IdentifiersOrDates(ApiHarvesterError):
    """Identifiers cannot be used in combination with dates."""


class ApiHarvesterConfigNotFound(ApiHarvesterError):
    """No ApiHarvesterConfig was found."""
