# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""API for manipulating items."""
from datetime import datetime, timezone
from functools import partial

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Q
from invenio_search import current_search_client

from rero_ils.modules.api import IlsRecordError, IlsRecordsIndexer, \
    IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.minters import id_minter
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref

from .circulation import ItemCirculation
from .issue import ItemIssue
from ..models import ItemIdentifier, ItemMetadata, ItemStatus

# provider
ItemProvider = type(
    'ItemProvider',
    (Provider,),
    dict(identifier=ItemIdentifier, pid_type='item')
)
# minter
item_id_minter = partial(id_minter, provider=ItemProvider)
# fetcher
item_id_fetcher = partial(id_fetcher, provider=ItemProvider)


class ItemsSearch(IlsRecordsSearch):
    """ItemsSearch."""

    class Meta:
        """Search only on item index."""

        index = 'items'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None

    def available_query(self):
        """Base elasticsearch query to compute availability.

        :returns: elasticsearch query.
        """
        must_not_filters = [
            # should not be masked
            Q('term', _masked=True),
            # should not be in_transit (even without loan)
            Q('term', status=ItemStatus.IN_TRANSIT),
            # if issue the status should be received
            Q('exists', field='issue') & ~Q('term', issue__status='received')
        ]

        if not_available_item_types := [
            hit.pid
            for hit in ItemTypesSearch()
            .source('pid')
            .filter('term', negative_availability=True)
            .scan()
        ]:
            # negative availability item type and not temporary item types
            has_items_filters = \
                    Q('terms', item_type__pid=not_available_item_types)
            has_items_filters &= ~Q('exists', field='temporary_item_type')
            # temporary item types with negative availability
            has_items_filters |= Q(
                'terms', temporary_item_type__pid=not_available_item_types)
            # add to the must not filters
            must_not_filters.append(has_items_filters)
        return self.filter(Q('bool', must_not=must_not_filters))


class Item(ItemCirculation, ItemIssue):
    """Item class."""

    minter = item_id_minter
    fetcher = item_id_fetcher
    provider = ItemProvider
    model_cls = ItemMetadata
    pids_exist_check = {
        'required': {
            'loc': 'location',
            'doc': 'document',
            'itty': 'item_type'
        },
        'not_required': {
            'org': 'organisation',
            # We can not make the holding required because it is created later
            'hold': 'holding'
        }
    }

    def delete_from_index(self):
        """Delete record from index."""
        try:
            ItemsIndexer().delete(self)
        except NotFoundError:
            pass

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        # local_fields aren't a reason to block suppression
        links.pop('local_fields', None)
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    def in_collection(self, **kwargs):
        """Get published collection pids for current item."""
        from ...collections.api import CollectionsSearch
        output = []
        search = CollectionsSearch() \
            .filter('term', items__pid=self.get('pid')) \
            .filter('term', published=True) \
            .sort({'title_sort': {'order': 'asc'}}) \
            .params(preserve_order=True) \
            .source(['pid', 'organisation', 'title', 'description'])
        orgs = {}
        for hit in search.scan():
            hit = hit.to_dict()
            org_pid = hit['organisation']['pid']
            if org_pid not in orgs:
                orgs[org_pid] = Organisation.get_record_by_pid(org_pid)
            collection_data = {
                'pid': hit['pid'],  # required property
                'title': hit['title'],  # required property
                'description': hit.get('description'),  # optional property
                'viewcode': orgs[org_pid].get('code')
            }
            collection_data = {k: v for k, v in collection_data.items() if v}
            output.append(collection_data)
        return output

    def replace_refs(self):
        """Replace $ref with real data."""
        tmp_itty_end_date = self.get('temporary_item_type', {}).get('end_date')
        tmp_loc_end_date = self.get('temporary_location', {}).get('end_date')
        data = super().replace_refs()
        if tmp_itty_end_date:
            data['temporary_item_type']['end_date'] = tmp_itty_end_date
        if tmp_loc_end_date:
            data['temporary_location']['end_date'] = tmp_loc_end_date
        return data

    @classmethod
    def get_item_record_for_ui(cls, **kwargs):
        """Return the item record for ui calls.

        retrieving the item record is possible from an item pid, barcode or
        from a loan.

        :param kwargs: contains at least one of item_pid, item_barcode, or pid.
        :return: the item record.
        """
        from ...loans.api import Loan
        item = None
        item_pid = kwargs.get('item_pid')
        item_barcode = kwargs.pop('item_barcode', None)
        loan_pid = kwargs.get('pid')
        if item_pid:
            item = Item.get_record_by_pid(item_pid)
        elif item_barcode:
            org_pid = kwargs.get(
                'organisation_pid', current_librarian.organisation_pid)
            item = Item.get_item_by_barcode(item_barcode, org_pid)
        elif loan_pid:
            item_pid = Loan.get_record_by_pid(loan_pid).item_pid
            item = Item.get_record_by_pid(item_pid)
        return item

    @classmethod
    def format_end_date(cls, end_date):
        """Return a formatted end date."""
        # (`datetime.now(timezone.utc)` by default)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        end_date = end_date.strftime('%Y-%m-%d')
        return end_date

    @classmethod
    def get_items_with_obsolete_temporary_item_type_or_location(
            cls, end_date=None):
        """Get all items with an obsolete temporary item_type or location.

        An end_date could be attached to the item temporary item_type or
        temporary location. If this date is less or equal to sysdate, then the
        temporary_item_type or temorary_location must be considered as obsolete
        and the field must be removed.

        :param end_date: the end_date to check.
        :return A generator of `ItemRecord` object.
        """
        end_date = cls.format_end_date(end_date)
        items_query = ItemsSearch()
        loc_es_quey = items_query.filter(
                    'range', temporary_location__end_date={'lte': end_date})
        locs = [
            (hit.meta.id, 'loc') for hit in loc_es_quey.source('pid').scan()]

        itty_es_query = items_query.filter(
                'range', temporary_item_type__end_date={'lte': end_date})
        itty = [(hit.meta.id, 'itty') for hit in itty_es_query.source(
            'pid').scan()]
        hits = itty + locs
        for id, field_type in hits:
            yield Item.get_record(id), field_type


class ItemsIndexer(IlsRecordsIndexer):
    """Indexing items in Elasticsearch."""

    record_cls = Item

    @classmethod
    def _es_item(cls, record):
        """Get the item from the corresponding index.

        :param record: an item object
        :returns: the elasticsearch document or {}
        """
        try:
            es_item = current_search_client.get(
                ItemsSearch.Meta.index, record.id)
            return es_item['_source']
        except NotFoundError:
            return {}

    @classmethod
    def _update_status_in_doc(cls, record, es_item):
        """Update the status of a given item in the document index.

        :param record: an item object
        :param es_item: a dict of the elasticsearch item
        """
        # retrieve the document in the corresponding es index
        document_pid = extracted_data_from_ref(record.get('document'))
        doc = next(
            DocumentsSearch()
            .extra(version=True)
            .filter('term', pid=document_pid)
            .scan()
        )
        # update the item status in the document
        data = doc.to_dict()
        for hold in data.get('holdings', []):
            for item in hold.get('items', []):
                if item['pid'] == record.pid:
                    item['status'] = record['status']
                    break
            else:
                continue
            break
        # reindex the document with the same version
        current_search_client.index(
            index=DocumentsSearch.Meta.index,
            id=doc.meta.id,
            body=data,
            version=doc.meta.version,
            version_type='external_gte')

    def index(self, record):
        """Index an item.

        :param record: an item object
        "returns: the elastiscsearch client result
        """
        from ...holdings.api import Holding

        # get previous indexed version
        es_item = self._es_item(record)

        # call the parent
        return_value = super().index(record)

        # fast document reindex for circulation operations
        if es_item and record.get('status') != es_item.get('status'):
            self._update_status_in_doc(record, es_item)
            return return_value

        # reindex the holding / doc for non circulation operations
        holding_pid = extracted_data_from_ref(record.get('holding'))
        holding = Holding.get_record_by_pid(holding_pid)
        holding.reindex()
        # reindex the old holding
        old_holding_pid = None
        if es_item:
            # reindex old holding ot update hte count
            old_holding_pid = es_item.get('holding', {}).get('pid')
            if old_holding_pid != holding_pid:
                old_holding = Holding.get_record_by_pid(old_holding_pid)
                old_holding.reindex()
        return return_value

    def delete(self, record):
        """Delete a record from index.

        :param record: Record instance.
        """
        from rero_ils.modules.holdings.api import Holding

        return_value = super().delete(record)
        holding_pid = extracted_data_from_ref(record.get('holding'))
        holding = Holding.get_record_by_pid(holding_pid)
        # delete only if a standard item
        deleted = False
        if not holding.is_serial:
            try:
                holding.delete(force=False, dbcommit=True, delindex=True)
                deleted = True
            except IlsRecordError.NotDeleted:
                pass
        if not deleted:
            # for items count
            holding.reindex()
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='item')
