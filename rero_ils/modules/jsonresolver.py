# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""General resolver."""

from flask import current_app
from invenio_pidstore.models import PersistentIdentifier


def resolve_json_refs(pid_type, pid):
    """Resolver for $ref in record.

    :param pid_type: type of pid
    :param pid: pid to resolve
    :return: resolved persistent identifier
    """
    try:
        persistent_id = PersistentIdentifier.get(pid_type, pid)
    except Exception as error:
        current_app.logger.error(f"Unable to resolve {pid_type} pid: {pid}")
        raise error

    if persistent_id.is_redirected():
        persistent_id = persistent_id.get_redirect()
    return {"pid": persistent_id.pid_value, "type": pid_type}
