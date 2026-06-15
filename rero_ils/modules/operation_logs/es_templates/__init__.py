# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""search index templates for Operation log records."""


def list_search_templates():
    """Search index templates path."""
    return ["rero_ils.modules.operation_logs.es_templates"]
