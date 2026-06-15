# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""LocalField dumpers."""

from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class ElasticSearchDumper(InvenioRecordsDumper):
    """LocalField dumper class for ElasticSearch integration."""

    def dump(self, record, data):
        """Dump a LocalField instance.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        output = {
            "organisation_pid": record.organisation_pid,
            "fields": record.get("fields", {}),
        }
        return data | output
