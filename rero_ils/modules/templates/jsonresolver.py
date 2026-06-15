# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Templates resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/templates/<pid>", host="bib.rero.ch")
def ill_request_resolver(pid):
    """Resolver for templates record."""
    return resolve_json_refs("tmpl", pid)
