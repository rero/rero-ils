# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

    It tries to extract from `record['$schema']` the index and doc_type.
    If it fails, return the default values.

    :param record: The record object.
    :returns: Tuple (index, doc_type).
    """
    index_names = current_search.mappings.keys()
    schema = record.get('$schema', '')
    if isinstance(schema, dict):
        schema = schema.get('$ref', '')

    # put all document in the same index
    # 'document-minimal-v0.0.1.json' becomes 'document-v0.0.1.json'
    if re.search(r'/documents/', schema):
        schema = re.sub(
            r'/document(?P<word>-\D+)?(?P<version>-v[\d,\.]+).json',
            r'/document\g<version>.json', schema)
    # authorities specific transformation
    if re.search(r'/authorities/', schema):
        schema = re.sub(r'/authorities/', '/persons/', schema)
        schema = re.sub(r'mef-person', 'person', schema)
    index, doc_type = schema_to_index(schema, index_names=index_names)

    if index and doc_type:
        return index, doc_type
    else:
        return (current_app.config['INDEXER_DEFAULT_INDEX'],
                current_app.config['INDEXER_DEFAULT_DOC_TYPE'])
