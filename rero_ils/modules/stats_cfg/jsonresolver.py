# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics configuration resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/stats_cfg/<pid>", host="bib.rero.ch")
def stats_cfg_resolver(pid):
    """Statistics configuration resolver."""
    return resolve_json_refs("stacfg", pid)
