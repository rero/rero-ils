# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""PatronTransactionEvent resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/patron_transaction_events/<pid>", host="bib.rero.ch")
def patron_transaction_event_resolver(pid):
    """Resolver for patron_transaction_event record."""
    return resolve_json_refs("ptre", pid)
