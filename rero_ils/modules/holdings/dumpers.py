# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Holdings dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class ClaimIssueHoldingDumper(InvenioRecordsDumper):
    """Dumper class use by claim issue notification for holding information."""

    def dump(self, record, data):
        """Dump a holdings instance with necessary information.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :returns: original data with addition holding information.
        :rtype: dict
        """
        assert record.is_serial, "Holding type must be 'serial'"
        data = {
            "pid": record.pid,
            "client_id": record.get("client_id"),
            "order_reference": record.get("order_reference"),
        }
        return {k: v for k, v in data.items() if v}
