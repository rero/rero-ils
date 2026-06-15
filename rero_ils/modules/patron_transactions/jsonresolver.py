# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron Transaction resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/patron_transactions/<pid>", host="bib.rero.ch")
def patron_transaction_resolver(pid):
    """Resolver for patron transaction record."""
    return resolve_json_refs("pttr", pid)
