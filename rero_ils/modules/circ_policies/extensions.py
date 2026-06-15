# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation policy record extensions."""

from invenio_records.extensions import RecordExtension


class CircPolicyFieldsExtension(RecordExtension):
    """Extension to manage circulation policy fields."""

    def _pickup_hold_duration_check(self, record):
        """Manage the pickup hold duration field.

        If the circulation policy doesn't allow request, no need to keep the
        `pickup_hold_duration` field.

        :param record: the record to check.
        """
        if not record.get("allow_requests") and "pickup_hold_duration" in record:
            del record["pickup_hold_duration"]

    pre_commit = _pickup_hold_duration_check
    pre_create = _pickup_hold_duration_check
