# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipt dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class AcqReceiptESDumper(InvenioRecordsDumper):
    """ElasticSearch dumper class for an AcqReceipt."""

    def dump(self, record, data):
        """Dump an AcqReceipt instance for ElasticSearch.

        For ElasticSearch integration, we need to dump basic informations from
        a `AcqReceipt` object instance, and add receipt date from related
        `AcqReceptionLine`.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        metadata = {
            "pid": record.pid,
            "reference": record.get("reference"),
            "receipt_date": list({line.get("receipt_date") for line in record.get_receipt_lines()}),
        }
        metadata = {k: v for k, v in metadata.items() if v}
        data.update(metadata)
        return data
