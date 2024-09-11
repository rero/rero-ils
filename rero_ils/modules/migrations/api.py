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

from elasticsearch_dsl import Document, Index, Keyword, Text
from elasticsearch_dsl.exceptions import ValidationException
from werkzeug.utils import import_string

from rero_ils.modules.libraries.api import Library

from .data.api import IndexCfg, MigrationData


class MigrationStatus(Enum):
    """Class holding all available migration statuses."""

    CREATED = "created"
    QUALITY_CONTROL = "quality control"
    DOCUMENT_DEDUPLICATION = "document deduplication"
    DONE = "done"


class Status(Keyword):
    """Migration Status."""

    def clean(self, data):
        """Clean validate and set the default value."""
        if data is None:
            data = MigrationStatus.CREATED.value
        try:
            MigrationStatus(data)
        except ValueError:
            raise ValidationException(
                f'The status value should be one of: {", ".join([item.value for item in MigrationStatus])}.'
            )
        return super().clean(data)


class Migration(Document):
    """Migration Resource (ElasticSearch only)."""

    name = Text(fields={"raw": Keyword()}, required=True)
    description = Text(fields={"raw": Keyword()})
    status = Status(required=True)
    library_pid = Keyword(required=True)
    organisation_pid = Keyword(required=True)
    conversion_code = Keyword(index=False, required=True)

    class Index:
        """Migration Index configuration."""

        name = "migrations-20240909"
        settings = {"number_of_shards": 2, "number_of_replicas": 2}
        aliases = {"migrations": {}}

    @property
    def conversion_class(self):
        """Class to perform the data conversion."""
        return import_string(self.conversion_code)

    @property
    def data_index_name(self):
        """Returns the index name based on the migration name."""
        return f"migration-data-{self.name}"

    @property
    def data_class(self):
        """Returns the class to create a migration data."""
        index = Index(name=self.data_index_name)
        index.settings(**IndexCfg.settings)
        index.aliases(**IndexCfg.aliases)
        cls = MigrationData.clone()
        return index.document(cls)

    @property
    def library(self):
        """Shortcut to get related library."""
        return Library.get_record_by_pid(self.library_pid)

    def _set_default_values(self):
        """Set the default values."""
        if self.organisation_pid is None and self.library:
            self.organisation_pid = self.library.organisation_pid
        # if not self.meta.id:
        self.meta["id"] = self.name

    def save(self, **kwargs):
        """Put the data on the elasticsearch index."""
        self._set_default_values()
        to_return = super().save(**kwargs)
        self.data_class.init()
        return to_return

    def delete(self, **kwargs):
        """Delete a migration record."""
        Index(self.data_index_name).delete()
        super().delete(*kwargs)
