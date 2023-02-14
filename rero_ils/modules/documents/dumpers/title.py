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

"""Title dumper."""
from invenio_records.dumpers import Dumper

from ..extensions import TitleExtension


class TitleDumper(Dumper):
    """Document title dumper."""

    def dump(self, record, data):
        """Dump a document by adding a string version of the title field.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        title_text = TitleExtension.format_text(
            record.get('title', []),
            responsabilities=record.get('responsibilityStatement')
        )
        data.update({
            'pid': record.get('pid'),
            'title_text': title_text
        })
        return data
