# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Item type resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/item_types/<pid>", host="bib.rero.ch")
def item_type_resolver(pid):
    """Item type resolver."""
    return resolve_json_refs("itty", pid)
