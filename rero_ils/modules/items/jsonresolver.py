# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Item resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/items/<pid>", host="bib.rero.ch")
def item_resolver(pid):
    """Item resolver."""
    return resolve_json_refs("item", pid)
