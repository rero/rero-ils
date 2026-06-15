# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/documents/<pid>", host="bib.rero.ch")
def document_resolver(pid):
    """Document resolver."""
    return resolve_json_refs("doc", pid)
