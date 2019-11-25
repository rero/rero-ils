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

import mock
import pytest
from utils import mock_response

from rero_ils.modules.documents.api import Document, document_id_fetcher
from rero_ils.modules.ebooks.tasks import create_records
from rero_ils.modules.persons.api import PersonsSearch


def test_document_create(db, document_data_tmp):
    """Test document creation."""
    ptty = Document.create(document_data_tmp, delete_pid=True)
    assert ptty == document_data_tmp
    assert ptty.get('pid') == '1'
    assert ptty.dumps()['editionStatement'][0]['_text'] == {
        'chi-hani': '第3版 / 曾令良主编',
        'default': 'Di 3 ban / Zeng Lingliang zhu bian'
    }
    ptty = Document.get_record_by_pid('1')
    assert ptty == document_data_tmp

    fetched_pid = document_id_fetcher(ptty.id, ptty)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'doc'


def test_document_can_not_delete(document, item_lib_martigny):
    """Test can not delete."""
    links = document.get_links_to_me()
    assert links['items'] == 1
    assert not document.can_delete


def test_document_can_delete(app, document_data_tmp):
    """Test can delete."""
    document = Document.create(document_data_tmp, delete_pid=True)
    assert document.get_links_to_me() == {}
    assert document.can_delete


def test_document_create_records(app, org_martigny, org_sion, ebook_1_data,
                                 ebook_2_data, item_type_online_martigny,
                                 loc_online_martigny, item_type_online_sion,
                                 loc_online_sion
                                 ):
    """Test can create harvested records."""
    ebook_1_data['electronic_location'] = [
        {
            "source": "ebibliomedia",
            "uri": "https://www.site1.org/ebook"
        }
    ]
    ebook_2_data['electronic_location'] = [
        {
            "source": "ebibliomedia",
            "uri": "https://www.site2.org/ebook"
        }
    ]
    n_created, n_updated = create_records([ebook_1_data])
    assert n_created == 1
    assert n_updated == 0

    ebook_1_data['electronic_location'] = [
        {
            "source": "ebibliomedia",
            "uri": "https://www.site2.org/ebook"
        },
        {
            "source": "mv-cantook",
            "uri": "https://www.site3.org/ebook"
        }
    ]
    n_created, n_updated = create_records([ebook_1_data, ebook_2_data])
    assert n_created == 1
    assert n_updated == 1

    ebook_1_data['electronic_location'] = [
        {
            "source": "mv-cantook",
            "uri": "https://www.site3.org/ebook"
        }
    ]
    n_created, n_updated = create_records([ebook_1_data, ebook_2_data])
    assert n_created == 0
    assert n_updated == 2

    # TODO: find a way to execute celery worker tasks in travis tests
    # n_created, n_updated = create_records([ebook_1_data])
    # assert n_created == 0
    # assert n_updated == 1


def test_document_can_delete_harvested(app, ebook_1_data):
    """Test can delete for harvested records."""
    document = Document.create(ebook_1_data, delete_pid=True)
    assert document.harvested
    assert not document.can_delete


def test_document_can_delete_with_loans(
        client, item_lib_martigny, loan_pending_martigny, document):
    """Test can delete a document."""
    links = document.get_links_to_me()
    assert 'items' in links
    assert 'loans' in links

    assert not document.can_delete

    reasons = document.reasons_not_to_delete()
    assert 'links' in reasons


# TODO: Delete person in enrich_document_data() from index after deletion
# @mock.patch('rero_ils.modules.documents.listener.requests_get')
# @mock.patch('rero_ils.modules.persons.jsonresolver.requests_get')
# def test_document_person_resolve(mock_resolver_get, mock_listener_get,
#                                  es_clear, db, document_ref,
#                                  person_response_data):
#     """Test document person resolve."""
#     mock_resolver_get.return_value = mock_response(
#         json_data=person_response_data
#     )
#     mock_listener_get.return_value = mock_response(
#         json_data=person_response_data
#     )

#     assert document_ref.replace_refs()[
#         'authors'
#     ][0]['pid'] == person_response_data['id']

#     count = PersonsSearch().filter(
#         'term',
#         pid=person_response_data['id']
#     ).count()
#     assert count == 1

#     document_ref.update(document_ref)
#     document_ref.delete()
#     count = PersonsSearch().filter(
#         'term',
#         pid=person_response_data['id']
#     ).count()
#     assert count == 0


def test_document_person_resolve_exception(es_clear, db, document_data_ref):
    """Test document person resolve."""
    with pytest.raises(Exception):
        Document.create(
            data=document_data_ref,
            delete_pid=False,
            dbcommit=True,
            reindex=True
        )
