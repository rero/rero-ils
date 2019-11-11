# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Define relation between records and buckets."""


class ElasticsearchIdentifier(dict):
    """Persistent identifiers for Elasticsearch record."""

    pid_value = None
    """Persistent Identifier."""

    pid_type = None
    """Persistent Identifier Type."""

    def __init__(self, pid_value, pid_type):
        """Initialize ElasticsearchIdentifier.

        :param pid_value: Elasticsearch identifier.
        :param pid_type: Elasticsearch identifier type.
        """
        self.pid_value = pid_value
        self.pid_type = pid_type

    @classmethod
    def create(cls, id, pid_type):
        """Create a persistent identifier for a given elasticsearch id.

        :param id: Elasticsearch ID.
        :param pid_type: Persistent identifier type.
        :returns: A :class:`rero_ils.models.ElasticsearchIdentifier`
            instance.
        """
        return cls(
            id,
            pid_type
        )
