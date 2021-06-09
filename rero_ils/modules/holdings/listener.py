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

"""Signals connector for Holding."""


from .api import HoldingsSearch
from ..items.api import ItemsSearch


def enrich_holding_data(sender, json=None, record=None, index=None,
                        doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == HoldingsSearch.Meta.index:
        library_pid = None
        organisation_pid = None
        # get the number of items for ui paging
        item_search = ItemsSearch()[0:0].filter(
            'term', holding__pid=record.pid)
        # to compute the number of masked item
        item_search.aggs.bucket('public_items', 'terms', field='_masked')
        results = item_search.source(['organisation', 'library']).execute()
        # number of items
        json['items_count'] = results.hits.total.value
        # number of masked items
        number_of_masked_items = 0
        for bucket in results.aggregations.public_items.buckets:
            if bucket.key_as_string == 'true':
                number_of_masked_items = bucket.doc_count
                break
        json['public_items_count'] = \
            json['items_count'] - number_of_masked_items
