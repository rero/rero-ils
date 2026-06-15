# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics record extensions."""

from invenio_records.extensions import RecordExtension

from rero_ils.modules.libraries.api import Library
from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.utils import extracted_data_from_ref

from .models import StatType


class StatisticsDumperExtension(RecordExtension):
    """Statistics extension defining record dumping behavior."""

    def pre_dump(self, record, data, dumper=None):
        """Called before a record is dumped.

        The statistics resource can have multiple values ; each value is
        related to a specific library. Depending on the connected user the
        record will be filtered keeping only values related to manageable
        libraries.

        :param record: the record to dump
        :param data: the data to dump.
        :param dumper: the dumper class used to dump the record.
        """
        # to filter the search list results
        if lib := record.get("config", {}).get("library"):
            lib_pid = lib.get("pid") or extracted_data_from_ref(lib.get("$ref"))
            org_pid = Library.get_record_by_pid(lib_pid).organisation_pid
            record["organisation"] = {"pid": org_pid}

        if not current_librarian:
            return

        if record["type"] == StatType.LIBRARIAN:
            library_pids = current_librarian.manageable_library_pids
            record["values"] = list(filter(lambda lib: lib["library"]["pid"] in library_pids, record["values"]))
