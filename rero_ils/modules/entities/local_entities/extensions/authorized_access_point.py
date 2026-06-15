# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Local entity extension to add authorized access point pid in the DB."""

from invenio_records.extensions import RecordExtension


class AuthorizedAccessPointExtension(RecordExtension):
    """Adds the authorized access point."""

    def _get_authorized_access_point(self, record):
        """."""
        # there is no language for local entities
        language = None
        return record.get_authorized_access_point(language)

    def pre_create(self, record):
        """Called before a record is created.

        :param record: the record metadata.
        """
        record["authorized_access_point"] = self._get_authorized_access_point(record)
        # required for validation
        if record.model:
            record.model.data = record

    def pre_commit(self, record):
        """Called before a record is committed.

        :param record: the record metadata.
        """
        record["authorized_access_point"] = self._get_authorized_access_point(record)
