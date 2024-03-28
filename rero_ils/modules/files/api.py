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

"""API for manipulating record file."""

from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.systemfields import IndexField
from rero_invenio_files.records.api import FileRecord
from rero_invenio_files.records.api import RecordWithFile as RecordWithFileBase


class RecordWithFile(RecordWithFileBase):
    """Object record with file API."""

    # Jsonschema
    schema = ConstantField("$schema", "local://files/record-v1.0.0.json")

    # Elasticsearch index
    index = IndexField("files-record-v1.0.0", search_alias="files")


FileRecord.record_cls = RecordWithFile
