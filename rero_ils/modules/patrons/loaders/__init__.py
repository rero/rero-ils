# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Loaders for `Patron` resources."""

from invenio_records_rest.loaders.marshmallow import marshmallow_loader

from ..schemas.json import PatronMetadataSchemaV1

json_v1 = marshmallow_loader(PatronMetadataSchemaV1)

__all__ = ("json_v1",)
