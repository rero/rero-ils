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
        if lib := record.get('config', {}).get('library'):
            lib_pid = (
                lib.get('pid')
                or extracted_data_from_ref(lib.get('$ref')))
            org_pid = Library.get_record_by_pid(lib_pid).organisation_pid
            record['organisation'] = {
                'pid': org_pid
            }

        if not current_librarian:
            return

        if record['type'] == StatType.LIBRARIAN:
            library_pids = current_librarian.manageable_library_pids
            record['values'] = list(filter(
                lambda lib: lib['library']['pid'] in library_pids,
                record['values']
            ))
