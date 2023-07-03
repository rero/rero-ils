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

"""Indexing dumper."""

from invenio_records.dumpers import Dumper


class EntityIndexerDumper(Dumper):
    """Entity indexer."""

    def dump(self, record, data):
        """Dump an entity instance.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data['resource_type'] = record.resource_type
        data['organisations'] = record.organisation_pids
        return data
