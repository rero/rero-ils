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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.documents.api import Document, DocumentsSearch, \
    document_id_fetcher


def test_document_create(db, document_data_tmp):
    """Test pttyanisation creation."""
    ptty = Document.create(document_data_tmp)
    assert ptty == document_data_tmp
    assert ptty.get('pid') == '1'

    ptty = Document.get_record_by_pid('1')
    assert ptty == document_data_tmp

    fetched_pid = document_id_fetcher(ptty.id, ptty)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'doc'


def test_document_es_mapping(es_clear, db, organisation,
                             document_data_tmp, item_on_loan):
    """."""
    search = DocumentsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Document.create(document_data_tmp, dbcommit=True, reindex=True)
    assert mapping == get_mapping(search.Meta.index)
