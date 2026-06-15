# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Title dumper."""

from invenio_records.dumpers import Dumper

from ..extensions import TitleExtension


class TitleDumper(Dumper):
    """Document title dumper."""

    def dump(self, record, data):
        """Dump a document by adding a string version of the title field.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        title_text = TitleExtension.format_text(
            record.get("title", []),
            responsabilities=record.get("responsibilityStatement"),
        )
        data.update({"pid": record.get("pid"), "title_text": title_text})
        return data
