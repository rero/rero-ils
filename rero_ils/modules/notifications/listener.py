# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for Notification."""

from .api import Notification, NotificationsSearch


def enrich_notification_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split("-")[0] == NotificationsSearch.Meta.index:
        if not isinstance(record, Notification):
            record = Notification.get_record_by_pid(record.get("pid"))
        json["organisation"] = {"pid": record.organisation_pid, "type": "org"}
