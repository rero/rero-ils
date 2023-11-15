# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
    schema = record.get('$schema', '')
    if isinstance(schema, dict):
        schema = schema.get('$ref', '')

    # authorities specific transformation
    if re.search(r'/mef/', schema):
        schema = re.sub(r'/mef/', '/remote_entities/', schema)
        schema = re.sub(r'mef-contribution', 'remote_entity', schema)

    if index := schema_to_index(schema, index_names=index_names):
        return index
    else:
        return current_app.config['INDEXER_DEFAULT_INDEX']
