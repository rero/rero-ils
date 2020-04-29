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

"""API for manipulating items."""


from functools import partial

from elasticsearch.exceptions import NotFoundError
from invenio_search import current_search

from .circulation import ItemCirculation
from .record import ItemRecord
from ..models import ItemIdentifier
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
        current_search.flush_and_refresh(DocumentsSearch.Meta.index)
        current_search.flush_and_refresh(cls.Meta.index)


class Item(ItemRecord, ItemCirculation):
    """Item class."""

    minter = item_id_minter
    fetcher = item_id_fetcher
    provider = ItemProvider

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

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        dump = super(Item, self).dumps(**kwargs)
        dump['available'] = self.available
        return dump


class ItemsIndexer(IlsRecordsIndexer):
    """Indexing items in Elasticsearch."""

    record_cls = Item

    def index(self, record):
        """Index an item."""
        from ...holdings.api import Holding
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
