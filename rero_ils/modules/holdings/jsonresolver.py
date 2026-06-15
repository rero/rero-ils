# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Holding resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/holdings/<pid>", host="bib.rero.ch")
def holding_resolver(pid):
    """Resolver for holding record."""
    return resolve_json_refs("hold", pid)
