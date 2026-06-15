# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Indexing dumper."""

from invenio_records.dumpers import Dumper


class EntityIndexerDumper(Dumper):
    """Entity indexer."""

    def dump(self, record, data):
        """Dump an entity instance.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data["resource_type"] = record.resource_type
        data["organisations"] = record.organisation_pids
        return data
