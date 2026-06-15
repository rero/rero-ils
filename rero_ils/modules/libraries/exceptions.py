# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries exceptions."""


class LibraryNeverOpen(Exception):
    """Raised when the library has no open days."""
