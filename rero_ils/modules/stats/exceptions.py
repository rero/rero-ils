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

"""Exceptions for statistics reports."""


class StatReportDistributionsValidatorException(Exception):
    """Error on validating distributions for statistics report."""


class NotActiveStatConfigException(Exception):
    """Error for non active statistics configuration."""

    def __init__(self, pid, *args, **kwargs):
        """Initialize exception."""
        self.pid = pid
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Exception as string."""
        return f'Statistics configuration pid: {self.pid} '\
            'is not active.'
