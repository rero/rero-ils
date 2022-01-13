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

"""Statistics methods about Library."""
from elasticsearch_dsl import A

from rero_ils.modules.documents.api import DocumentsSearch


def get_document_type_repartition(library, document_type=None, excludes=None):
    """Get the number document type grouped by library.

    :param library: the library to analyze.
    :param document_type: the main document type filter. If present the output
                          response will be the repartition by document subtype.
    :param excludes: a list of values to exclude from response.
    :return a dictionary of statistics representing the repartition by document
            type about document belonging to the library.
    """
    excludes = excludes or []
    query = DocumentsSearch()[:0]\
        .filter('term', holdings__organisation__library_pid=library.pid)
    if document_type:
        query = query.filter('term', type__main_type=document_type)
    aggr_field = 'type.subtype' if document_type else 'type.main_type'
    query.aggs.bucket(
        'document_type',
        A('terms', field=aggr_field, missing='none')
    )
    results = query.execute()

    agg_result = results.aggregations.document_type
    data = {hit['key']: hit['doc_count'] for hit in agg_result.buckets}
    if agg_result['sum_other_doc_count']:
        data['other'] = agg_result['sum_other_doc_count']

    return {k: v for k, v in data.items() if k not in excludes}
