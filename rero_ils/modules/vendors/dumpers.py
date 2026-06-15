# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Vendores dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class VendorAcquisitionNotificationDumper(InvenioRecordsDumper):
    """Vendor dumper class for acquisition order notification."""

    def dump(self, record, data):
        """Dump a vendor instance for acquisition order notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update(
            {
                "name": record.get("name"),
                "language": record.get("communication_language", "eng"),
                "email": record.order_email,
            }
        )
        return {k: v for k, v in data.items() if v}


class VendorClaimIssueNotificationDumper(InvenioRecordsDumper):
    """Vendor dumper class for claim issue notification."""

    def dump(self, record, data):
        """Dump a vendor instance for claim issue notification.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update(
            {
                "name": record.get("name"),
                "language": record.get("communication_language", "eng"),
                "email": record.serial_email,
            }
        )
        return {k: v for k, v in data.items() if v}
