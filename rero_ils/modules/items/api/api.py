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
from functools import partial

from elasticsearch.exceptions import NotFoundError
from invenio_search import current_search

from .circulation import ItemCirculation
from .issue import ItemIssue
from .record import ItemRecord
from ..models import ItemIdentifier, ItemMetadata
from ...api import IlsRecordError, IlsRecordsIndexer, IlsRecordsSearch
from ...documents.api import Document, DocumentsSearch
from ...fetchers import id_fetcher
from ...minters import id_minter
from ...providers import Provider

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

    @classmethod
    def flush(cls):
        """Flush indexes."""
        from rero_ils.modules.holdings.api import HoldingsSearch
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        current_search.flush_and_refresh(HoldingsSearch.Meta.index)
        current_search.flush_and_refresh(cls.Meta.index)


class Item(ItemRecord, ItemCirculation, ItemIssue):
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

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        Ensures that only one note of each type is present.

        :returns: False if notes array has multiple notes with same type
        """
        note_types = [note.get('type') for note in self.get('notes', [])]
        return len(note_types) == len(set(note_types))

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
        if self.item_record_type == 'issue' and self.issue_is_regular:
            cannot_delete['others'] = dict(
                regular_issue_cannot_be_deleted=True
            )
        return cannot_delete

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        dump = super(Item, self).dumps(**kwargs)
        dump['available'] = self.available
        return dump

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
        item_pid = kwargs.get('item_pid', None)
        item_barcode = kwargs.pop('item_barcode', None)
        loan_pid = kwargs.get('pid', None)
        if item_pid:
            item = Item.get_record_by_pid(item_pid)
        elif item_barcode:
            item = Item.get_item_by_barcode(item_barcode)
        elif loan_pid:
            item_pid = Loan.get_record_by_pid(loan_pid).item_pid
            item = Item.get_record_by_pid(item_pid)
        return item


class ItemsIndexer(IlsRecordsIndexer):
    """Indexing items in Elasticsearch."""

    record_cls = Item

    def index(self, record):
        """Index an item."""
        from ...holdings.api import Holding, HoldingsSearch

        # get the old holding record if exists
        items = ItemsSearch().filter(
            'term', pid=record.get('pid')
        ).source().execute().hits

        holding_pid = None
        if items.total:
            item = items.hits[0]['_source']
            holding_pid = item.get('holding', {}).get('pid')

        return_value = super(ItemsIndexer, self).index(record)
        document_pid = record.replace_refs()['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        current_search.flush_and_refresh(HoldingsSearch.Meta.index)

        # check if old holding can be deleted
        if holding_pid:
            holding_rec = Holding.get_record_by_pid(holding_pid)
            try:
                # TODO: Need to split DB and elasticsearch deletion.
                holding_rec.delete(force=False, dbcommit=True, delindex=True)
            except IlsRecordError.NotDeleted:
                pass

        return return_value

    def delete(self, record):
        """Delete a record.

        :param record: Record instance.
        """
        from ...holdings.api import Holding

        return_value = super(ItemsIndexer, self).delete(record)
        rec_with_refs = record.replace_refs()
        document_pid = rec_with_refs['document']['pid']
        document = Document.get_record_by_pid(document_pid)
        document.reindex()
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)

        holding = rec_with_refs.get('holding', '')
        if holding:
            holding_rec = Holding.get_record_by_pid(holding.get('pid'))
            try:
                # TODO: Need to split DB and elasticsearch deletion.
                holding_rec.delete(force=False, dbcommit=True, delindex=True)
            except IlsRecordError.NotDeleted:
                pass

        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(ItemsIndexer, self).bulk_index(record_id_iterator,
                                             doc_type='item')
