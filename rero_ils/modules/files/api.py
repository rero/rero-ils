# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating record file."""

from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.systemfields import IndexField
from rero_invenio_files.records.api import FileRecord
from rero_invenio_files.records.api import RecordWithFile as RecordWithFileBase


class RecordWithFile(RecordWithFileBase):
    """Object record with file API."""

    # Jsonschema
    schema = ConstantField("$schema", "local://files/record-v1.0.0.json")

    # search index
    index = IndexField("files-record-v1.0.0", search_alias="files")


FileRecord.record_cls = RecordWithFile
