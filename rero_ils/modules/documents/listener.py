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

"""."""

from ..documents.api import DocumentsSearch
from ..items.api import Item
from ..locations.api import Location


def enrich_document_data(sender, json=None, record=None, index=None,
                         **dummy_kwargs):
    """Signal sent before a record is indexed.

    Arguments:
    - ``json``: The dumped record dictionary which can be modified.
    - ``record``: The record being indexed.
    - ``index``: The index in which the record will be indexed.
    - ``doc_type``: The doc_type for the record.
    """
    # TODO: this multiply the indexing time by 5, try an other way!
    document_index_name = DocumentsSearch.Meta.index
    if index.startswith(document_index_name):
        items = []
        available = False
        for item_pid in Item.get_items_pid_by_document_pid(record['pid']):
            item = Item.get_record_by_pid(item_pid)
            available = available or item.available
            location = Location.get_record_by_pid(
                item.replace_refs()['location']['pid']).replace_refs()
            items.append({
                'pid': item.pid,
                'barcode': item['barcode'],
                'status': item['status'],
                'library_pid': location['library']['pid']
            })
        if items:
            json['items'] = items
            json['available'] = available
