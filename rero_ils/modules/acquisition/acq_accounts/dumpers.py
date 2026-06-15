# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition account dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class AcqAccountGenericDumper(InvenioRecordsDumper):
    """AcqAccount generic dumper class."""

    def dump(self, record, data):
        """Dump an `AcqAccount` instance with basic informations.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        # Keep only some attributes from AcqOrderLine object initial dump
        for attr in ["pid", "name", "number"]:
            if value := record.get(attr):
                data.update({attr: value})
        return {k: v for k, v in data.items() if v}
