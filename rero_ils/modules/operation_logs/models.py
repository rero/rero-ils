# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Models and constants for OperationLogs."""


class OperationLogOperation:
    """Allowed operation for operation logs."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
