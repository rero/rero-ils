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

"""Document Record tests."""

from __future__ import absolute_import, print_function

import pytest

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.documents.api import Document, document_id_fetcher
from rero_ils.modules.ebooks.tasks import create_records


def test_document_create(db, document_data_tmp):
    """Test document creation."""
    ptty = Document.create(document_data_tmp, delete_pid=True)
    assert ptty == document_data_tmp
    assert ptty.get('pid') == '1'
    assert ptty.dumps()['editionStatement'][0]['_text'] == [
        {'language': 'chi-hani', 'value': '第3版 / 曾令良主编'},
        {'language': 'default', 'value': 'Di 3 ban / Zeng Lingliang zhu bian'}
    ]
    doc = Document.get_record_by_pid('1')
    assert doc == document_data_tmp
    assert doc.document_type == 'docsubtype_other_book'

    fetched_pid = document_id_fetcher(ptty.id, ptty)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'doc'

    with pytest.raises(IlsRecordError.PidAlreadyUsed):
        new_doc = Document.create(doc)


def test_document_add_cover_url(db, document):
    """Test add url."""
    document.add_cover_url(url='http://images.rero.ch/cover.png')
    assert document.get('electronicLocator') == [{
        'content': 'coverImage',
        'type': 'relatedResource',
        'url': 'http://images.rero.ch/cover.png'
    }]
    # don't add the same url
    document.add_cover_url(url='http://images.rero.ch/cover.png')
    assert document.get('electronicLocator') == [{
        'content': 'coverImage',
        'type': 'relatedResource',
        'url': 'http://images.rero.ch/cover.png'
    }]


def test_document_can_not_delete(document, item_lib_martigny):
    """Test can not delete."""
    can, reasons = document.can_delete
    assert not can
    assert reasons['links']['items']


def test_document_can_delete(app, document_data_tmp):
    """Test can delete."""
    document = Document.create(document_data_tmp, delete_pid=True)
    can, reasons = document.can_delete
    assert can
    assert reasons == {}


def test_document_create_records(app, org_martigny, org_sion, ebook_1_data,
                                 ebook_2_data, item_type_online_martigny,
                                 loc_online_martigny, item_type_online_sion,
                                 loc_online_sion
                                 ):
    """Test can create harvested records."""
    ebook_1_data['electronicLocator'] = [
        {
            "source": "ebibliomedia",
            "url": "https://www.site1.org/ebook",
            "type": "resource"
        }
    ]
    ebook_2_data['electronicLocator'] = [
        {
            "source": "ebibliomedia",
            "url": "https://www.site2.org/ebook",
            "type": "resource"
        }
    ]
    n_created, n_updated = create_records([ebook_1_data])
    assert n_created == 1
    assert n_updated == 0

    ebook_1_data['electronicLocator'] = [
        {
            "source": "ebibliomedia",
            "url": "https://www.site2.org/ebook",
            "type": "resource"
        },
        {
            "source": "mv-cantook",
            "url": "https://www.site3.org/ebook",
            "type": "resource"
        }
    ]
    n_created, n_updated = create_records([ebook_1_data, ebook_2_data])
    assert n_created == 1
    assert n_updated == 1

    ebook_1_data['electronicLocator'] = [
        {
            "source": "mv-cantook",
            "url": "https://www.site3.org/ebook",
            "type": "resource"
        }
    ]
    n_created, n_updated = create_records([ebook_1_data, ebook_2_data])
    assert n_created == 0
    assert n_updated == 2

    # TODO: find a way to execute celery worker tasks in travis tests
    # n_created, n_updated = create_records.delay([ebook_1_data])
    # assert n_created == 0
    # assert n_updated == 1


def test_document_can_delete_harvested(app, ebook_1_data):
    """Test can delete for harvested records."""
    document = Document.create(ebook_1_data, delete_pid=True)
    can, reasons = document.can_delete
    assert document.harvested
    assert not can
    assert reasons['others']['harvested']


def test_document_can_delete_with_loans(
        client, item_lib_martigny, loan_pending_martigny, document):
    """Test can delete a document."""
    can, reasons = document.can_delete
    assert not can
    assert reasons['links']['items']
    assert reasons['links']['loans']


def test_document_contribution_resolve_exception(es_clear, db,
                                                 document_data_ref):
    """Test document contribution resolve."""
    document_data_ref['contribution'] = [{
        '$ref': 'https://mef.rero.ch/api/agents/rero/XXXXXX'
    }],
    with pytest.raises(Exception):
        Document.create(
            data=document_data_ref,
            delete_pid=False,
            dbcommit=True,
            reindex=True
        )
