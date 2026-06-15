# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/local_entities/<pid>", host="bib.rero.ch")
def local_entities_resolver(pid):
    """Resolver for local entity record."""
    return resolve_json_refs("locent", pid)
