# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Location resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/locations/<pid>", host="bib.rero.ch")
def location_resolver(pid):
    """Location resolver."""
    return resolve_json_refs("loc", pid)
