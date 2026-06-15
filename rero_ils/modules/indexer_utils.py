# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utility functions for indexer data processing."""

import re

from flask import current_app
from invenio_indexer.utils import schema_to_index
from invenio_search import current_search


def record_to_index(record):
    """Get index/doc_type given a record.

    It tries to extract from `record['$schema']` the index.
    If it fails, return the default values.

    :param record: The record object.
    :return: index.
    """
    index_names = current_search.mappings.keys()
    schema = record.get("$schema", "")
    if isinstance(schema, dict):
        schema = schema.get("$ref", "")

    # authorities specific transformation
    if re.search(r"/mef/", schema):
        schema = re.sub(r"/mef/", "/remote_entities/", schema)
        schema = re.sub(r"mef-contribution", "remote_entity", schema)

    if index := schema_to_index(schema, index_names=index_names):
        return index
    return current_app.config["INDEXER_DEFAULT_INDEX"]
