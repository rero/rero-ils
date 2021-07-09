# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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
from datetime import datetime
from functools import partial

from elasticsearch.exceptions import NotFoundError
from invenio_search import current_search_client

from .circulation import ItemCirculation
from .issue import ItemIssue
from ..models import ItemIdentifier, ItemMetadata
from ...api import IlsRecordError, IlsRecordsIndexer, IlsRecordsSearch
from ...documents.api import DocumentsSearch
from ...fetchers import id_fetcher
from ...minters import id_minter
from ...organisations.api import Organisation
from ...patrons.api import current_librarian
from ...providers import Provider
from ...utils import extracted_data_from_ref

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

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        loans = self.get_number_of_loans()
        if loans:
            links['loans'] = loans
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
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
        data = super().replace_refs()
        if tmp_itty_end_date:
            data['temporary_item_type']['end_date'] = tmp_itty_end_date
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
    def get_items_with_obsolete_temporary_item_type(cls, end_date=None):
        """Get all items with an obsolete temporary item_type.

        An end_date could be attached to the item temporary item_type. If this
        date is less or equal to sysdate, then the temporary_item_type must be
        considered as obsolete.

        :param end_date: the end_date to check (`datetime.now()` by default)
        :return A generator of `ItemRecord` object.
        """
        if end_date is None:
            end_date = datetime.utcnow()
        end_date = end_date.strftime('%Y-%m-%d')
        results = ItemsSearch() \
            .filter('range', temporary_item_type__end_date={'lte': end_date}) \
            .source('pid') \
            .scan()
        for result in results:
            yield Item.get_record_by_pid(result.pid)


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
        """Delete a record.

        :param record: Record instance.
        """
        from ...holdings.api import Holding

        return_value = super().delete(record)
        holding_pid = extracted_data_from_ref(record.get('holding'))
        holding = Holding.get_record_by_pid(holding_pid)
        # delete only if a standard item
        deleted = False
        if not holding.is_serial:
            try:
                # delete only if a standard item
                if not holding.is_serial:
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
