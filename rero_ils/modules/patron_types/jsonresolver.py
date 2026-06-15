# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron type resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/patron_types/<pid>", host="bib.rero.ch")
def patron_type_resolver(pid):
    """Patron type resolver."""
    return resolve_json_refs("ptty", pid)
