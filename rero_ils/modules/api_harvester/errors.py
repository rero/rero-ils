# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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
