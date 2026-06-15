# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Persistent identifier fetchers."""

from collections import namedtuple

from rero_ils.modules.utils import get_pid_type_from_schema

FetchedPID = namedtuple("FetchedPID", ["pid_type", "pid_value"])
"""A pid fetcher."""


def id_fetcher(record_uuid, data):
    """Fetch a record's identifier.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :return: A :data:`rero_ils.modules.fetchers.FetchedPID` instance.
    """
    pid_type = "ent"
    # try to extract pid type from schema
    if schema := data.get("$schema"):
        pid_type = get_pid_type_from_schema(schema)
    return FetchedPID(pid_type=pid_type, pid_value=data["pid"])
