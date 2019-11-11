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

"""Internal resolver for persistant identifiers."""

from __future__ import absolute_import, print_function

from elasticsearch.exceptions import NotFoundError


class ElasticsearchResolver(object):
    """Elasticsearch identifier resolver.

    Helper class for retrieving an internal object for a given
    elasticsearch identifier.
    """

    def __init__(self, pid_type=None, object_type=None, getter=None):
        """Initialize resolver.

        :param pid_type: Elasticsearch identifier type.
        :param object_type: Object type.
        :param getter: Callable that will take an object id for the given
            object type and retrieve the internal object.
        """
        self.pid_type = pid_type
        self.object_type = object_type
        self.object_getter = getter

    def resolve(self, pid_value):
        """Resolve an elasticsearch pid to an internal object.

        :param pid_value: Elasticsearch identifier.
        :returns: A tuple containing (pid, object).
        """
        record = self.object_getter(pid_value) if pid_value else None
        if not record:
            raise NotFoundError(self.pid_type, pid_value)
        return record.persistent_identifier, record
