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

"""Acquisition api record."""

from abc import ABC

from rero_ils.modules.api import IlsRecord


class AcquisitionIlsRecord(IlsRecord, ABC):
    """Abstract acquisition resource record."""

    def __str__(self):
        """Human-readable record string representation."""
        output = f'[{self.provider.pid_type}#{self.pid}]'
        if 'name' in self:
            output += f" {self['name']}"
        return output

    def __repr__(self):
        """Full representation of the record."""
        return super().__repr__()
