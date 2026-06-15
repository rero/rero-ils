# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
