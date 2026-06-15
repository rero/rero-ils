# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Indexing dumper."""

from flask import current_app
from invenio_records.dumpers import Dumper

from rero_ils.modules.entities.models import EntityResourceType


class BaseDocumentEntityDumper(Dumper):
    """Base document Entity dumper class."""

    def dump(self, record, data):
        """Dump an entity instance.

        This dumper this

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data = {
            "type": record["type"],
            "pid": record.pid,
            "pids": {record.resource_type: record.pid},
        }
        if record.resource_type == EntityResourceType.REMOTE:
            for agency in current_app.config["RERO_ILS_AGENTS_SOURCES"]:
                if field := record.get(agency):
                    data["type"] = field.get("type", record["type"])
                    data["pids"][agency] = record[agency]["pid"]

            variant_access_points = []
            parallel_access_points = []
            for source in record.get("sources"):
                variant_access_points += record[source].get("variant_access_point", [])
                parallel_access_points += record[source].get("parallel_access_point", [])
            if variant_access_points:
                data["variant_access_point"] = variant_access_points
            if parallel_access_points:
                data["parallel_access_point"] = parallel_access_points
        return data
