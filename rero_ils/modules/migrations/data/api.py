# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration API."""

from datetime import UTC, datetime
from enum import Enum

from invenio_search.engine import dsl


def _(x):
    """Identity function used to trigger string extraction."""
    return x


class IndexCfg:
    """Migration Data Index configuration."""

    aliases = {"migration-data": {}}


class DeduplicationStatus(Enum):
    """Class holding all available migration statuses."""

    PENDING = _("pending")
    ERROR = _("error")
    CHECK = _("check")
    MULTIPLE_MATCH = _("multiple match")
    NO_MATCH = _("no match")
    MATCH = _("match")


class Status(dsl.Keyword):
    """Migration Status."""

    def clean(self, data):
        """Clean validate and set the default value."""
        try:
            DeduplicationStatus(data)
        except ValueError:
            raise dsl.ValidationException(
                f"The status value should be one of: {', '.join([item.value for item in DeduplicationStatus])}."
            )
        return super().clean(data)


class DeduplicationCandidate(dsl.InnerDoc):
    """Deduplication candidate."""

    # ILS pid
    pid = dsl.Keyword(required=True)
    # score between 0 and 1
    score = dsl.Float()
    # score explanations
    detailed_score = dsl.Object(dynamic=True)
    # resource content
    json = dsl.Object(required=True, dynamic=True)


class Deduplication(dsl.InnerDoc):
    """Deduplication data."""

    # deduplication statuses
    status = Status(required=True)
    # list of candidates
    candidates = dsl.Object(DeduplicationCandidate, multi=True)
    # log messages
    logs = dsl.Object(dynamic=True)
    # related ils pid
    ils_pid = dsl.Keyword()
    # split the data into several subsets
    subset = dsl.Keyword()
    # manually modified by
    modified_by = dsl.Text(fields={"raw": dsl.Keyword()})
    # manually modified at
    modified_at = dsl.Date(default_timezone="UTC")


class Conversion(dsl.InnerDoc):
    """Conversion data."""

    # conversion status
    status = dsl.Keyword(required=True)
    # converted JSON data
    json = dsl.Object(dynamic=True)
    # log messages
    logs = dsl.Object(dynamic=True)


class MigrationData(dsl.Document):
    """Migration Resource (OpenSearch only)."""

    # migration ID
    migration_id = dsl.Text(fields={"raw": dsl.Keyword()}, required=True)
    # blob containing the original data
    raw = dsl.Binary(required=True)
    # related organistion pid computed from the library migration
    organisation_pid = dsl.Keyword(required=True)
    # conversion data
    conversion = dsl.Object(Conversion, required=True, multi=False)
    # deduplication data
    deduplication = dsl.Object(Deduplication, required=True, multi=False)
    # creation date
    created_at = dsl.Date(default_timezone="UTC")
    # modification date
    updated_at = dsl.Date(default_timezone="UTC")

    @classmethod
    def clone(cls):
        """Clone the current class.

        It is required as the class member will be changed.
        """

        class Cloned(cls):
            pass

        return Cloned

    @property
    def migration(self):
        """Shortcut to get related library."""
        from ..api import Migration

        if self.migration_id:
            return Migration.get(id=self.migration_id)
        return None

    def _set_default_values(self):
        """Set the default values."""
        if self.organisation_pid is None and self.migration:
            self.organisation_pid = self.migration.organisation_pid
        if not self.deduplication:
            self.deduplication = Deduplication(status="pending")
        if not self.conversion:
            self.conversion = Conversion(status="pending")
        if self.migration and self.migration.conversion_class and self.raw:
            _id, converted, status, logs = self.migration.conversion_class.convert(self.raw)
            self.conversion.json = converted
            if _id:
                self.meta["id"] = _id
            if status:
                self.conversion.status = status
            if logs:
                self.conversion.logs = logs
        if self.created_at is None:
            self.created_at = datetime.now(UTC)

    def save(self, **kwargs):
        """Put the data on the search index."""
        _id = self._set_default_values()
        self.updated_at = datetime.now(UTC)
        return super().save(**kwargs)
