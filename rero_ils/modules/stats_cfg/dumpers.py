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

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper


class IndexerDumper(Dumper):
    """Stat configuration dumper."""

    def dump(self, record, data):
        """Dump a stat configuration.

        Adds the organisation information.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data['organisation'] = dict(pid=record.organisation_pid)
        return data


# dumper used for indexing
indexer_dumper = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    ReplaceRefsDumper(),
    IndexerDumper()
])
