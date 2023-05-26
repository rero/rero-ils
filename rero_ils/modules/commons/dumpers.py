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

"""Record dumpers."""
import contextlib

from invenio_records.api import _records_state
from invenio_records.dumpers import Dumper as InvenioRecordsDumper


class MultiDumper(InvenioRecordsDumper):
    """Aggregate several dumpers."""

    def __init__(self, dumpers=None):
        """Constructor.

        :param dumpers: list - list of dumpers to aggregate.
        """
        super().__init__()
        self._dumpers = dumpers or []

    def dump(self, record, data):
        """Dump a record that can be used a source document.

        Iterate over all dumpers to process one after the other.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        for dumper in self._dumpers:
            with contextlib.suppress(AttributeError):
                data = dumper.dump(record, data)
        return data

    def load(self, data, record_cls):
        """Load a record from the source document of a search engine hit.

        Iterate over all dumpers to process one after the other.

        :param data: A Python dictionary representing the data to load.
        :param records_cls: The record class to be constructed.
        :returns: A instance of ``record_cls``.
        """
        for dumper in self._dumpers:
            with contextlib.suppress(AttributeError):
                record_cls = dumper.load(data, record_cls)
        return record_cls


class ReplaceRefsDumper(InvenioRecordsDumper):
    """Replace link data in resource."""

    def dump(self, record, data):
        """Dump record data by replacing `$ref` links.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        :return a dict with dumped data.
        """
        from copy import deepcopy
        return deepcopy(_records_state.replace_refs(data))
