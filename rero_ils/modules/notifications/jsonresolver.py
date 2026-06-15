# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Notifications resolver."""

import jsonresolver

from ..jsonresolver import resolve_json_refs


@jsonresolver.route("/api/notifications/<pid>", host="bib.rero.ch")
def notification_resolver(pid):
    """Resolver for notifications record."""
    return resolve_json_refs("notif", pid)
