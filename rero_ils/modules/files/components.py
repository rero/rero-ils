# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Files components."""

from invenio_records_resources.services.files.components import \
    FileServiceComponent

from .operations import ReindexDoc


class DocumentReindexComponent(FileServiceComponent):
    """Component to reindex document linked to the file record."""

    def _register(self, record):
        """Register a document reindex operation."""
        doc_pid = record["metadata"]["links"][0].replace("doc_", "")
        operation = ReindexDoc(doc_pid)
        if operation not in self.uow._operations:
            self.uow.register(operation)

    def commit_file(self, identity, id_, file_key, record):
        """Commit file handler."""
        self._register(record)

    def update_file_metadata(self, identity, id_, file_key, record, data):
        """Update file metadata handler."""
        self._register(record)

    def delete_file(self, identity, id_, file_key, record, deleted_file):
        """Delete file handler."""
        self._register(record)

    def delete_all_files(self, identity, id_, record, results):
        """Delete all files handler."""
        self._register(record)
