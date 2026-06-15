# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration API."""

from datetime import UTC, datetime
from enum import Enum

from elasticsearch_dsl import Date, Document, Index, Keyword, Text
from elasticsearch_dsl.exceptions import ValidationException
from werkzeug.utils import import_string

from rero_ils.modules.libraries.api import Library

from .data.api import IndexCfg, MigrationData


def _(x):
    """Identity function used to trigger string extraction."""
    return x


class MigrationStatus(Enum):
    """Class holding all available migration statuses."""

    CREATED = _("created")
    QUALITY_CONTROL = _("quality control")
    DOCUMENT_DEDUPLICATION = _("document deduplication")
    DONE = _("done")


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
                f"The status value should be one of: {', '.join([item.value for item in MigrationStatus])}."
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
    updated_at = Date(default_timezone="UTC")
    created_at = Date(default_timezone="UTC")

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
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        self.meta["id"] = self.name

    def save(self, **kwargs):
        """Put the data on the search index."""
        self._set_default_values()
        self.updated_at = datetime.now(UTC)
        to_return = super().save(**kwargs)
        self.data_class.init()
        return to_return

    def delete(self, **kwargs):
        """Delete a migration record."""
        Index(self.data_index_name).delete()
        super().delete(**kwargs)
