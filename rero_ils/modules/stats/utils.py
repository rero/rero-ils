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

"""Utility functions for Statistics."""

from rero_ils.modules.stats.models import StatDistributions


def swap_distributions_required(distributions: list):
    """Swap distributions to process data for report."""
    if (distributions[0] in [StatDistributions.TIME_RANGE_MONTH,
                             StatDistributions.TIME_RANGE_YEAR]
        and distributions[1]) \
        or distributions[1] in [StatDistributions.LIBRARY,
                                StatDistributions.ITEM_OWNING_LIBRARY]:
        return True
    return False
