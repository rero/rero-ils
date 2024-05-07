# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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
