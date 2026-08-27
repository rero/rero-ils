# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Files results classes."""

from flask import current_app
from invenio_records_resources.services.files.results import FileList


class MainFileList(FileList):
    """List of file items result."""

    @property
    def entries(self):
        """Iterator over the hits."""
        record_id = self._record.get("id")
        for entry in self._results:
            if (metadata := entry.metadata) is None:
                # Every file is expected to carry a metadata entry, an empty one for an uploaded file and a typed
                # one for the thumbnails and the full texts. Missing it altogether is not a shape this code
                # produces, so the file is reported and left out rather than guessed about.
                current_app.logger.error("File without metadata, record: %s file: %s", record_id, entry.key)
                continue
            # keep only the main files
            if metadata.get("type") in ["fulltext", "thumbnail"]:
                continue
            projection = self._service.file_schema.dump(
                entry,
                context={
                    "identity": self._identity,
                },
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, entry)

            yield projection
