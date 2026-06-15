# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
