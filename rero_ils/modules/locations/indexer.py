# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Indexing method for `Location` resource."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper


class LocationIndexerDumper(Dumper):
    """ElasticSearch indexer class for `Location` resource."""

    def dump(self, record, data):
        """Dump a `Location` instance with for ElasticSearch indexing.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data["organisation"] = {"pid": record.organisation_pid, "type": "org"}
        return data


location_replace_refs_dumper = MultiDumper(dumpers=[Dumper(), ReplaceRefsDumper()])

location_indexer_dumper = MultiDumper(dumpers=[Dumper(), ReplaceRefsDumper(), LocationIndexerDumper()])
