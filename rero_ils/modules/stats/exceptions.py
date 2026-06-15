# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
        return f"Statistics configuration pid: {self.pid} is not active."
