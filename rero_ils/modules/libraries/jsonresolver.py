# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Libraries resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/libraries/<pid>", host="bib.rero.ch")
def library_resolver(pid):
    """Library resolver."""
    return resolve_json_refs("lib", pid)
