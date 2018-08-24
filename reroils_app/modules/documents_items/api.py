# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating items associated to a document."""

from invenio_search.api import RecordsSearch

from ..api import RecordWithElements
from ..documents.api import Document
from ..documents.fetchers import document_id_fetcher
from ..documents.minters import document_id_minter
from ..documents.providers import DocumentProvider
from ..items.api import Item
from .models import DocumentsItemsMetadata


class DocumentsSearch(RecordsSearch):
    """RecordsSearch for borrowed documents."""

    class Meta:
        """Search only on documents index."""

        index = 'documents'


class DocumentsWithItems(RecordWithElements):
    """Api for Documents with Items."""

    record = Document
    element = Item
    metadata = DocumentsItemsMetadata
    elements_list_name = 'itemslist'
    minter = document_id_minter
    fetcher = document_id_fetcher
    provider = DocumentProvider

    # @property
    # def elements(self):
    #     """Return an array of Items."""
    #     if self.model is None:
    #         raise MissingModelError()
    #     # retrive all items in the relation table
    #     # sorted by item creation date
    #     documents_items = self.metadata.query\
    #         .filter_by(document_id=self.id)\
    #         .join(self.metadata.item)\
    #         .order_by(RecordMetadata.created)
    #     to_return = []
    #     for doc_item in documents_items:
    #         item = Item.get_record_by_id(doc_item.item.id)
    #         to_return.append(item)
    #     return to_return

    @property
    def itemslist(self):
        """Itemslist."""
        return self.elements

    @property
    def available(self):
        """Get availability for loan."""
        available = False
        for item in self.itemslist:
            available = available or item.available
        return available

    def add_item(self, item, dbcommit=False, reindex=False):
        """Add an item."""
        super(DocumentsWithItems, self).add_element(
            item,
            dbcommit=dbcommit,
            reindex=reindex
        )

    def remove_item(self, item, force=False, delindex=False):
        """Remove an item."""
        super(DocumentsWithItems, self).remove_element(
            item,
            force=force,
            delindex=delindex
        )

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        data = super(DocumentsWithItems, self).dumps(**kwargs)
        data['available'] = self.available
        return data

    @classmethod
    def get_document_by_itemid(cls, id_, with_deleted=False):
        """Retrieve the record by id."""
        return super(DocumentsWithItems, cls).get_record_by_elementid(
            id_, with_deleted
        )
