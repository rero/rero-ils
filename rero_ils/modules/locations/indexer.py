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

"""Indexing method for `Location` resource."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper


class LocationIndexerDumper(Dumper):
    """ElasticSearch indexer class for `Location` resource."""

    def dump(self, record, data):
        """Dump a `Location` instance with for ElasticSearch indexing.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data['organisation'] = {
            'pid': record.organisation_pid,
            'type': 'org'
        }
        return data


location_replace_refs_dumper = MultiDumper(dumpers=[
    Dumper(),
    ReplaceRefsDumper()
])

location_indexer_dumper = MultiDumper(dumpers=[
    Dumper(),
    ReplaceRefsDumper(),
    LocationIndexerDumper()
])
