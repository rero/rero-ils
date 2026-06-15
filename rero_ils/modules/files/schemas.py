# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Files support for the RERO invenio instances."""

from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import Schema, fields, pre_load
from marshmallow_utils.fields import SanitizedUnicode


class MetadataSchema(Schema):
    """Record metadata schema class."""

    collections = fields.List(SanitizedUnicode())
    library = fields.Dict(required=True)
    document = fields.Dict(required=True)
    n_files = fields.Int(dump_only=True)
    file_size = fields.Int(dump_only=True)

    @pre_load
    def remove_fields(self, data, **kwargs):
        """Removes computed fields.

        :param data: Dict of record data.
        :returns: Modified data.
        """
        data.pop("n_files", None)
        data.pop("file_size", None)
        return data


class RecordSchema(BaseRecordSchema):
    """Service schema for subjects."""

    metadata = fields.Nested(MetadataSchema)
