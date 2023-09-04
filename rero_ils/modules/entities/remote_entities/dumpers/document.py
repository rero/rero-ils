# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
from flask import current_app
from invenio_records.dumpers import Dumper


class DocumentEntityDumper(Dumper):
    """Remote entity indexer."""

    def dump(self, record, data):
        """Dump a remote entity instance.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data = {'pid': record.pid}
        for agency in current_app.config['RERO_ILS_AGENTS_SOURCES']:
            if field := record.get(agency):
                data['type'] = field.get('bf:Agent', record['type'])
                data[f'id_{agency}'] = record[agency]['pid']

        variant_access_points = []
        parallel_access_points = []
        for source in record.get('sources'):
            variant_access_points += record[source].get(
                'variant_access_point', [])
            parallel_access_points += record[source].get(
                'parallel_access_point', [])
        if variant_access_points:
            data['variant_access_point'] = variant_access_points
        if parallel_access_points:
            data['parallel_access_point'] = parallel_access_points

        return data
