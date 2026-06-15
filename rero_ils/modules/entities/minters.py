# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Persistent identifier minters."""

from collections import namedtuple

EntityMinter = namedtuple("EntityMinter", ["pid_type", "pid_value", "object_uuid", "object_type"])


def id_minter(record_uuid, data, provider, pid_key="pid", object_type="rec"):
    """RERO ILS dummy minter."""
    # DEV NOTES:
    # A minter is required for invenio-records-rest.
    # This return a dummy PersistentIdentifier
    return EntityMinter(
        pid_type=object_type,
        pid_value=data["pid"],
        object_uuid=record_uuid,
        object_type=object_type,
    )
