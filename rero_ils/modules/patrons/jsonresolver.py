# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/patrons/<pid>", host="bib.rero.ch")
def patron_resolver(pid):
    """Patron resolver."""
    return resolve_json_refs("ptrn", pid)
