# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Files results classes."""

from invenio_records_resources.services.files.results import FileList


class MainFileList(FileList):
    """List of file items result."""

    @property
    def entries(self):
        """Iterator over the hits."""
        for entry in self._results:
            # keep only the main files
            if entry.metadata.get("type") in ["fulltext", "thumbnail"]:
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
