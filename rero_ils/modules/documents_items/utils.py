# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Utilities functions for rero-ils."""

from flask import url_for
from invenio_indexer.api import RecordIndexer

from ..documents_items.api import DocumentsWithItems
from ..items.api import Item
from ..utils import clean_dict_keys


def delete_item(record_type, record_class, pid):
    """Remove an item from a document.

    The item is marked as deleted in the db, his pid as well.
    The document is reindexed.
    """
    item = record_class.get_record_by_pid(pid)
    document = DocumentsWithItems.get_document_by_itemid(item.id)
    item.delete(delindex=False)
    document.remove_item(item, delindex=True)
    RecordIndexer().client.indices.flush()
    _next = url_for('invenio_records_ui.doc', pid_value=document.pid)
    return _next, item.pid


def save_item(data, record_type, record_class, parent_pid):
    """Save a record into the db and index it.

    If the item does not exists, it will be created
    and attached to the parent document.
    """
    pid = data.get('pid')
    data = clean_dict_keys(data)
    if pid:
        item = record_class.get_record_by_pid(pid)
        item.update(data, dbcommit=False)
        document = DocumentsWithItems.get_document_by_itemid(item.id)
    else:
        item = Item.create(data, dbcommit=False)
        document = DocumentsWithItems.get_record_by_pid(parent_pid)
        document.add_item(item, dbcommit=False, reindex=False)
    document.dbcommit(reindex=True)
    RecordIndexer().client.indices.flush()
    _next = url_for('invenio_records_ui.doc', pid_value=document.pid)
    return _next, item.pid
