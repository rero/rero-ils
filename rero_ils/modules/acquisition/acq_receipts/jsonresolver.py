# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition Receipt resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/acq_receipts/<pid>", host="bib.rero.ch")
def acq_receipt_resolver(pid):
    """Resolver for acquisition receipt record."""
    return resolve_json_refs("acre", pid)
