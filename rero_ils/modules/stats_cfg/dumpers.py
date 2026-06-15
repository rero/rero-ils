# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Indexing dumper."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper


class IndexerDumper(Dumper):
    """Stat configuration dumper."""

    def dump(self, record, data):
        """Dump a stat configuration.

        Adds the organisation information.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data["organisation"] = {"pid": record.organisation_pid}
        return data


# dumper used for indexing
indexer_dumper = MultiDumper(
    dumpers=[
        # make a fresh copy
        Dumper(),
        ReplaceRefsDumper(),
        IndexerDumper(),
    ]
)
