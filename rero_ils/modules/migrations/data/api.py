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

"""Migration API."""

from datetime import datetime, timezone
from enum import Enum

from elasticsearch_dsl import (
    Binary,
    Date,
    Document,
    Float,
    InnerDoc,
    Keyword,
    Object,
    Text,
)
from elasticsearch_dsl.exceptions import ValidationException


def _(x):
    """Identity function used to trigger string extraction."""
    return x


class IndexCfg:
    """Migration Data Index configuration."""

    settings = {"number_of_shards": 2, "number_of_replicas": 2}
    aliases = {"migration-data": {}}


class DeduplicationStatus(Enum):
    """Class holding all available migration statuses."""

    PENDING = _("pending")
    ERROR = _("error")
    CHECK = _("check")
    MULTIPLE_MATCH = _("multiple match")
    NO_MATCH = _("no match")
    MATCH = _("match")


class Status(Keyword):
    """Migration Status."""

    def clean(self, data):
        """Clean validate and set the default value."""
        try:
            DeduplicationStatus(data)
        except ValueError:
            raise ValidationException(
                f"The status value should be one of: {', '.join([item.value for item in DeduplicationStatus])}."
            )
        return super().clean(data)


class DeduplicationCandidate(InnerDoc):
    """Deduplication candidate."""

    # ILS pid
    pid = Keyword(required=True)
    # score between 0 and 1
    score = Float()
    # score explanations
    detailed_score = Object(dynamic=True)
    # resource content
    json = Object(required=True, dynamic=True)


class Deduplication(InnerDoc):
    """Deduplication data."""

    # deduplication statuses
    status = Status(required=True)
    # list of candidates
    candidates = Object(DeduplicationCandidate, multi=True)
    # log messages
    logs = Object(dynamic=True)
    # related ils pid
    ils_pid = Keyword()
    # split the data into several subsets
    subset = Keyword()
    # manually modified by
    modified_by = Text(fields={"raw": Keyword()})
    # manually modified at
    modified_at = Date(default_timezone="UTC")


class Conversion(InnerDoc):
    """Conversion data."""

    # conversion status
    status = Keyword(required=True)
    # converted JSON data
    json = Object(dynamic=True)
    # log messages
    logs = Object(dynamic=True)


class MigrationData(Document):
    """Migration Resource (ElasticSearch only)."""

    # migration ID
    migration_id = Text(fields={"raw": Keyword()}, required=True)
    # blob containing the original data
    raw = Binary(required=True)
    # related organistion pid computed from the library migration
    organisation_pid = Keyword(required=True)
    # conversion data
    conversion = Object(Conversion, required=True, multi=False)
    # deduplication data
    deduplication = Object(Deduplication, required=True, multi=False)
    # creation date
    created_at = Date(default_timezone="UTC")
    # modification date
    updated_at = Date(default_timezone="UTC")

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
            _id, converted, status, logs = self.migration.conversion_class.convert(
                self.raw
            )
            self.conversion.json = converted
            if _id:
                self.meta["id"] = _id
            if status:
                self.conversion.status = status
            if logs:
                self.conversion.logs = logs
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def save(self, **kwargs):
        """Put the data on the elasticsearch index."""
        _id = self._set_default_values()
        self.updated_at = datetime.now(timezone.utc)
        return super().save(**kwargs)
