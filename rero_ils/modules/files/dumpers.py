# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Files indexer dumpers."""

from copy import deepcopy

from invenio_records.api import _records_state
from invenio_records.dumpers import SearchDumperExt


class FileInformationDumperExt(SearchDumperExt):
    """File information dumper extension."""

    def dump(self, record, data):
        """Dump additional information.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        data.update(deepcopy(_records_state.replace_refs(data)))
        n_main_files = 0
        size = 0
        # inject files informations
        for f in record.files:
            file = record.files[f]
            f_type = file.get("type")
            # main files only
            if f_type not in ["fulltext", "thumbnail"]:
                n_main_files += 1
            # main files or extracted text
            if f_type != "thumbnail" and record.files[f].file:
                size += record.files[f].file.size
        data["metadata"]["n_files"] = n_main_files
        data["metadata"]["file_size"] = size
        lib_pid = data["metadata"]["library"]["pid"]
        from rero_ils.modules.libraries.api import Library

        org_pid = Library.get_record_by_pid(lib_pid).organisation_pid
        data["metadata"]["organisation"] = {"pid": org_pid, "type": "doc"}
