# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Vendor resolver."""

import jsonresolver
from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus


@jsonresolver.route("/api/vendors/<pid>", host="bib.rero.ch")
def vendor_resolver(pid):
    """Resolver for vendor record."""
    persistent_id = PersistentIdentifier.get("vndr", pid)
    if persistent_id.status == PIDStatus.REGISTERED:
        return {"pid": persistent_id.pid_value}
    current_app.logger.error(f"Doc resolver error: /api/vendors/{pid} {persistent_id}")
    raise Exception("unable to resolve")
