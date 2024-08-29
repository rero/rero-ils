# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Migration API."""
from enum import Enum

from elasticsearch_dsl import Document, Keyword, Text

from rero_ils.modules.libraries.api import Library


class MigrationError:
    """Base class for migration errors."""

    class ValidationError(Exception):
        """Validation Error."""


class MigrationStatus(Enum):
    """Class holding all available migration statuses."""

    CREATED = "created"
    QUALITY_CONTROL = "quality control"
    DOCUMENT_DEDUPLICATION = "document deduplication"
    DONE = "done"


class Migration(Document):
    """Migration Resource (ElasticSearch only)."""

    name = Text(fields={"raw": Keyword()})
    description = Text(fields={"raw": Keyword()})
    status = Keyword()
    library_pid = Keyword()
    organisation_pid = Keyword()

    class Index:
        """Migration Index configuration."""

        name = "migrations-20240909"
        settings = {"number_of_shards": 2, "number_of_replicas": 2}
        aliases = {"migrations": {}}

    @property
    def library(self):
        """Shortcut to get related library."""
        return Library.get_record_by_pid(self.library_pid)

    def save(self, **kwargs):
        """Put the data on the elasticsearch index."""
        if not self.name:
            raise MigrationError.ValidationError("name is required")
        if not self.library_pid:
            raise MigrationError.ValidationError("library_pid is required")
        if not self.status:
            self.status = MigrationStatus.CREATED.value
        try:
            MigrationStatus(self.status)
        except ValueError:
            raise MigrationError.ValidationError(
                f'The status value should be one of: {", ".join([item.value for item in MigrationStatus])}.'
            )
        self.organisation_pid = self.library.organisation_pid
        return super().save(**kwargs)
