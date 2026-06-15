# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""AcqAccount resolver."""

import jsonresolver

from rero_ils.modules.jsonresolver import resolve_json_refs


@jsonresolver.route("/api/acq_accounts/<pid>", host="bib.rero.ch")
def acq_account_resolver(pid):
    """Resolver for acq_account record."""
    return resolve_json_refs("acac", pid)
