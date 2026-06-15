# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition Order resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/acq_orders/<pid>", host="bib.rero.ch")
def acq_order_resolver(pid):
    """Resolver for acquisition order record."""
    return resolve_json_refs("acor", pid)
