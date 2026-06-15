# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ILLRequest resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/ill_requests/<pid>", host="bib.rero.ch")
def ill_request_resolver(pid):
    """Resolver for ill_request record."""
    return resolve_json_refs("illr", pid)
