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

"""Exception about acquisition resources."""

from invenio_records.errors import RecordsError


class BudgetDoesNotExist(RecordsError):
    """Error raised when acquisition budget record doest not exist."""


class RolloverError(Exception):
    """Generic error for rollover process."""


class InactiveBudgetError(RolloverError):
    """Inactive budget exception."""

    def __init__(self, pid_value, *args, **kwargs):
        """Initialize exception."""
        self.pid_value = pid_value
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Exception as string."""
        return f"Budget#{self.pid_value} is inactive"


class IncompatibleBudgetError(RolloverError):
    """When two budget aren't compatible with each other."""

    def __init__(self, pid1_value, pid2_value, *args, **kwargs):
        """Initialize exception."""
        self.pid1 = pid1_value
        self.pid2 = pid2_value
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Exception as string."""
        return f"Budget#{self.pid1} isn' compatible with Budget#{self.pid2}"


class BudgetNotEmptyError(RolloverError):
    """When a budget are linked children resources."""

    def __init__(self, pid, *args, **kwargs):
        """Initialize exception."""
        self.pid = pid
        super().__init__(*args, **kwargs)

    def __str__(self):
        """Exception as string."""
        return f"Budget#{self.pid} are some linked children resources."
