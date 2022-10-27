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

"""Signals connector for Holding."""


from elasticsearch_dsl.query import Q
from invenio_db import db

from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.tasks import process_bulk_queue
from rero_ils.modules.utils import extracted_data_from_ref, get_ref_for_pid

from .api import Holding, HoldingsSearch
from ..items.api import Item, ItemsIndexer, ItemsSearch


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

        holding = next(HoldingsSearch()
                       .filter('term', pid=record.pid)
                       .source('holdings_type').scan(), None)
        # get the number of items for ui paging
        item_search = ItemsSearch()[0:0]\
            .filter('term', holding__pid=record.pid)

        if holding is not None and holding["holdings_type"] == 'serial':
            item_search = ItemsSearch()[0:0]\
                .filter('term', holding__pid=record.pid)\
                .filter('term', issue__status="received")

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


def update_items_locations_and_types(sender, record=None, **kwargs):
    """This method checks if the items of the parent record needs an update.

    This method checks the location and item_type of each item attached to the
    holding record and update the item record accordingly.
    This method should be connect with 'after_record_update'.
    :param record: the holding record.
    """
    if isinstance(record, Holding) and \
            record.get('holdings_type') == HoldingTypes.SERIAL:
        # identify all items records attached to this serials holdings record
        # with different location and item_type.
        hold_circ_pid = record.circulation_category_pid
        hold_loc_pid = record.location_pid
        search = ItemsSearch().filter('term', holding__pid=record.pid)
        item_hits = search.\
            filter('bool', should=[
                        Q('bool', must_not=[
                            Q('match', item_type__pid=hold_circ_pid)]),
                        Q('bool', must_not=[
                            Q('match', location__pid=hold_loc_pid)])])\
            .source(['pid'])
        items = [hit.meta.id for hit in item_hits.scan()]
        items_to_index = []
        # update these items and make sure they have the same location/category
        # as the parent holdings record.
        for id in items:
            try:
                item = Item.get_record(id)
                if not item:
                    continue
                items_to_index.append(id)
                item_temp_loc_pid, item_temp_type_pid = None, None
                # remove the item temporary_location if it is equal to the
                # new item location.
                temporary_location = item.get('temporary_location', {})
                if temporary_location:
                    item_temp_loc_pid = extracted_data_from_ref(
                        temporary_location.get('$ref'))
                if hold_loc_pid != item.location_pid:
                    if item_temp_loc_pid == hold_loc_pid:
                        item.pop('temporary_location', None)
                    item['location'] = {'$ref': get_ref_for_pid(
                        'locations', hold_loc_pid)}
                # remove the item temporary_item_type if it is equal to the
                # new item item_type.
                temporary_type = item.get('temporary_item_type', {})
                if temporary_type:
                    item_temp_type_pid = extracted_data_from_ref(
                        temporary_type.get('$ref'))
                if hold_circ_pid != item.item_type_pid:
                    if item_temp_type_pid == hold_circ_pid:
                        item.pop('temporary_item_type', None)
                    item['item_type'] = {'$ref': get_ref_for_pid(
                        'item_types', hold_circ_pid)}
                # update directly in database.
                db.session.query(item.model_cls).filter_by(id=item.id).update(
                    {item.model_cls.json: item})
            except Exception as err:
                pass
        if items_to_index:
            # commit session
            db.session.commit()
            # bulk indexing of item records.
            indexer = ItemsIndexer()
            indexer.bulk_index(items_to_index)
            process_bulk_queue.apply_async()
