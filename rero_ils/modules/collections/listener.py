# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Signals connector for Collection."""

from .api import Collection, CollectionsSearch
from ..utils import extracted_data_from_ref


def enrich_collection_data(sender, json=None, record=None, index=None,
                           doc_type=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == CollectionsSearch.Meta.index:
        collection = record
        if not isinstance(record, Collection):
            collection = Collection.get_record_by_pid(record.get('pid'))
        json['organisation'] = {
            'pid': extracted_data_from_ref(collection.get('organisation')),
            'type': 'org'
        }
