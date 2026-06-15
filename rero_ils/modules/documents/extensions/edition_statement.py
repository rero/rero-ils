# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document record extension to enrich the edition statement."""

from invenio_records.extensions import RecordExtension

from rero_ils.dojson.utils import remove_trailing_punctuation

from ..utils import display_alternate_graphic_first


class EditionStatementExtension(RecordExtension):
    """Adds textual information for editionStatement."""

    @classmethod
    def format_text(cls, edition):
        """Format edition for _text."""
        designations = edition.get("editionDesignation", [])
        responsibilities = edition.get("responsibility", [])
        designation_output = {}
        for designation in designations:
            language = designation.get("language", "default")
            value = designation.get("value", "")
            designation_output[language] = value
        responsibility_output = {}
        for responsibility in responsibilities:
            language = responsibility.get("language", "default")
            value = responsibility.get("value", "")
            responsibility_output[language] = value

        edition_text = []
        for key, value in designation_output.items():
            designation = designation_output.get(key)
            responsibility = responsibility_output.get(key, "")
            value = remove_trailing_punctuation(f"{designation} / {responsibility}")
            if display_alternate_graphic_first(key):
                edition_text.insert(0, {"value": value, "language": key})
            else:
                edition_text.append({"value": value, "language": key})
        return edition_text

    def post_dump(self, record, data, dumper=None):
        """Called before a record is dumped.

        :param record: invenio record - the original record.
        :param data: dict - the data.
        :param dumper: record dumper - dumper helper.
        """
        editions = data.get("editionStatement", [])
        for edition in editions:
            edition["_text"] = self.format_text(edition)
