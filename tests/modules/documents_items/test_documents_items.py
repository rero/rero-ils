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

"""Minters module tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

from invenio_records.models import RecordMetadata

from rero_ils.modules.documents_items.api import DocumentsWithItems
from rero_ils.modules.documents_items.models import DocumentsItemsMetadata
from rero_ils.modules.documents_items.views import abstracts_format, \
    authors_format, publishers_format, series_format
from rero_ils.modules.items.api import Item
from rero_ils.modules.locations.api import Location
from rero_ils.modules.members_locations.api import MemberWithLocations


def test_create(db, minimal_document_record, minimal_item_record,
                minimal_member_record, minimal_location_record):
    """Test DocumentWithItems creation."""
    memb = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    loc = Location.create(minimal_location_record, dbcommit=True)
    memb.add_location(loc, dbcommit=True)
    minimal_item_record['location_pid'] = loc.pid
    item = Item.create(minimal_item_record, dbcommit=True)
    doc = DocumentsWithItems.create(minimal_document_record, dbcommit=True)
    assert doc.itemslist == []

    doc.add_item(item, dbcommit=True)
    assert doc.itemslist[0] == item

    dump = doc.dumps()
    assert dump['itemslist'][0] == item.dumps()


def test_delete_item(app,
                     minimal_document_record, minimal_item_record):
    """Test DocumentWithItems item deletion."""
    doc = DocumentsWithItems.create(minimal_document_record)
    item = Item.create(minimal_item_record)
    doc.add_item(item)
    doc.dbcommit()
    pid = item.persistent_identifier
    assert pid.is_registered()
    doc.remove_item(item, force=True)
    doc.dbcommit()
    assert True
    assert pid.is_deleted()
    assert doc.itemslist == []

    item1 = Item.create(minimal_item_record)
    doc.add_item(item1)
    item2 = Item.create(minimal_item_record)
    doc.add_item(item2)
    item3 = Item.create(minimal_item_record)
    doc.add_item(item3)
    doc.dbcommit()
    doc.remove_item(item2, force=True)
    doc.dbcommit()
    assert len(doc.itemslist) == 2
    assert doc.itemslist[0]['pid'] == '2'
    assert doc.itemslist[1]['pid'] == '4'


def test_delete_document(app,
                         minimal_document_record, minimal_item_record):
    """Test DocumentWithItems deletion."""
    doc_count = DocumentsItemsMetadata.query.count()
    rec_count = RecordMetadata.query.count()
    doc = DocumentsWithItems.create(minimal_document_record)
    item1 = Item.create(minimal_item_record, dbcommit=True)
    pid1 = item1.persistent_identifier
    doc.add_item(item1)
    item2 = Item.create(minimal_item_record, dbcommit=True)
    pid2 = item2.persistent_identifier
    doc.add_item(item2)
    item3 = Item.create(minimal_item_record, dbcommit=True)
    pid3 = item3.persistent_identifier
    doc.add_item(item3)
    doc.dbcommit()
    assert DocumentsItemsMetadata.query.count() == doc_count + 3
    assert RecordMetadata.query.count() == rec_count + 4
    assert pid1.is_registered()
    assert pid2.is_registered()
    assert pid3.is_registered()
    doc.delete(force=True)
    assert DocumentsItemsMetadata.query.count() == doc_count
    assert RecordMetadata.query.count() == rec_count
    assert pid1.is_deleted()
    assert pid2.is_deleted()
    assert pid3.is_deleted()


def test_authors_format(document_data_authors):
    """Test authors format."""
    result = 'Foo; Bar, prof, 2018'
    assert result == authors_format(document_data_authors)


def test_publishers_format(document_data_publishers):
    """Test publishers format."""
    result = 'Foo; place1; place2: Foo; Bar'
    assert result == publishers_format(document_data_publishers)


def test_series_format(document_data_series):
    """Test series format."""
    result = 'serie 1; serie 2, 2018'
    assert result == series_format(document_data_series)


def test_abstracts_format(document_data_abstracts):
    """Test series format."""
    result = 'line1\nline2\nline3'
    assert result == abstracts_format(document_data_abstracts)
