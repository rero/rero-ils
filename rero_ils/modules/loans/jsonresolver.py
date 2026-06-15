# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Loan resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/loans/<pid>", host="bib.rero.ch")
def loan_resolver(pid):
    """Loan resolver."""
    return resolve_json_refs("loanid", pid)
