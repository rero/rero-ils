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

"""Document mapping tests."""

from elasticsearch_dsl.query import MultiMatch
from utils import get_mapping

from rero_ils.modules.documents.api import Document, DocumentsSearch


def test_document_search_mapping(
    app, document_records
):
    """Test document search mapping."""
    search = DocumentsSearch()

    c = search.query('query_string', query='reine Berthe').count()
    assert c == 2

    c = search.query('query_string', query='maison').count()
    assert c == 1

    c = search.query('query_string', query='scene').count()
    assert c == 1

    query = MultiMatch(query='scène', fields=['abstracts.fre'])
    c = search.query(query).count()
    assert c == 1

    c = search.query('query_string', query='Körper').count()
    assert c == 1

    query = MultiMatch(query='Körper', fields=['abstracts.ger'])
    c = search.query(query).count()
    assert c == 1

    c = search.query('query_string', query='Chamber Secrets').count()
    assert c == 1

    query = MultiMatch(query='Chamber of Secrets', fields=['title.eng'])
    c = search.query(query).count()
    assert c == 1


def test_document_es_mapping(db, org_martigny,
                             document_data_tmp, item_lib_martigny):
    """Test document elasticsearch mapping."""
    search = DocumentsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Document.create(
        document_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
