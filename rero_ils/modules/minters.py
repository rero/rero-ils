# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Persistent identifier minters."""


def id_minter(record_uuid, data, provider, pid_key="pid", object_type="rec"):
    """RERO ILS minter."""
    provider = provider.create(object_type=object_type, object_uuid=record_uuid, pid_value=data.get(pid_key))

    persistent_identifier = provider.pid
    data[pid_key] = persistent_identifier.pid_value
    return persistent_identifier
