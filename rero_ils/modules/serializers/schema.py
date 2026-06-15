# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO ILS Record schema for serialization."""

from invenio_records_rest.schemas import RecordSchemaJSONV1 as _RecordSchemaJSONV1
from marshmallow import fields


class RecordSchemaJSONV1(_RecordSchemaJSONV1):
    """Schema for records RERO ILS in JSON.

    Add permissions & explanation fields.
    """

    permissions = fields.Raw()
    explanation = fields.Raw()
