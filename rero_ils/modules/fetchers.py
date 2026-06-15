# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Persistent identifier fetchers."""

from collections import namedtuple

FetchedPID = namedtuple("FetchedPID", ["provider", "pid_type", "pid_value"])
"""A pid fetcher."""


def id_fetcher(record_uuid, data, provider, pid_key="pid"):
    """Fetch a record's identifier.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :return: A :data:`rero_ils.modules.fetchers.FetchedPID` instance.
    """
    return FetchedPID(provider=provider, pid_type=provider.pid_type, pid_value=data[pid_key])
