# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Organisation resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/organisations/<pid>", host="bib.rero.ch")
def organisation_resolver(pid):
    """Organisation resolver."""
    return resolve_json_refs("org", pid)
