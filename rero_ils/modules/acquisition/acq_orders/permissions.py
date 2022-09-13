# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Permissions for Acquisition order."""

from rero_ils.modules.permissions import AcquisitionPermission

from .api import AcqOrder


class AcqOrderPermission(AcquisitionPermission):
    """Acquisition order permissions."""

    @classmethod
    def _rolled_over(cls, record):
        """Check if record attached to rolled over budget.

        :param record: Record to check.
        :return: True if action can be done.
        """
        # ensure class type for sent record
        if not isinstance(record, AcqOrder):
            record = AcqOrder(record)
        return record.is_active
