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

from elasticsearch_dsl import Binary, Document, Keyword, Object, Text


class IndexCfg:
    """Migration Data Index configuration."""

    settings = {"number_of_shards": 2, "number_of_replicas": 2}
    aliases = {"migration-data": {}}


class MigrationData(Document):
    """Migration Resource (ElasticSearch only)."""

    migration_id = Text(fields={"raw": Keyword()}, required=True)
    raw = Binary(required=True)
    organisation_pid = Keyword(required=True)
    json = Object(dynamic=True)
    conversion_logs = Object(dynamic=True)
    conversion_status = Keyword(required=True)

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

    def _set_default_values(self):
        """Set the default values."""
        if self.organisation_pid is None and self.migration:
            self.organisation_pid = self.migration.organisation_pid
        if self.migration and self.migration.conversion_class and self.raw:
            _id, converted, status, logs = self.migration.conversion_class.convert(
                self.raw
            )
            # print(_id, converted)
            self.json = converted
            if _id:
                self.meta["id"] = _id
            if status:
                self.conversion_status = status
            if logs:
                self.conversion_logs = logs

    def save(self, **kwargs):
        """Put the data on the elasticsearch index."""
        _id = self._set_default_values()
        return super().save(**kwargs)
