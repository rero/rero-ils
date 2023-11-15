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

from copy import deepcopy

import mock
import pytest
from invenio_db import db
from jsonschema.exceptions import ValidationError
from utils import flush_index, mock_response

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.documents.api import Document, DocumentsSearch, \
    document_id_fetcher
from rero_ils.modules.documents.models import DocumentIdentifier
from rero_ils.modules.ebooks.tasks import create_records
from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.entities.remote_entities.api import \
    RemoteEntitiesSearch, RemoteEntity
from rero_ils.modules.entities.remote_entities.utils import \
    extract_data_from_mef_uri
from rero_ils.modules.tasks import process_bulk_queue


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
        Document.create(doc)


@mock.patch('requests.Session.get')
def test_document_create_with_mef(
        mock_contributions_mef_get, app, document_data_ref, document_data,
        entity_person_data, entity_person_response_data):
    """Load document with mef records reference."""
    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )
    assert RemoteEntitiesSearch().count() == 0
    doc = Document.create(
        data=deepcopy(document_data_ref),
        delete_pid=False, dbcommit=False, reindex=False)
    doc.reindex()
    flush_index(DocumentsSearch.Meta.index)
    doc = Document.get_record_by_pid(doc.get('pid'))
    assert doc['contribution'][0]['entity']['pid'] == entity_person_data['pid']
    hit = DocumentsSearch().get_record_by_pid(doc.pid).to_dict()

    assert hit['contribution'][0]['entity']['pid'] == entity_person_data['pid']
    assert hit['contribution'][0]['entity']['primary_source'] == 'rero'
    assert RemoteEntitiesSearch().count() == 1
    contrib = RemoteEntity.get_record_by_pid(entity_person_data['pid'])
    contrib.delete_from_index()
    doc.delete_from_index()
    db.session.rollback()

    assert not Document.get_record_by_pid(doc.get('pid'))
    assert not RemoteEntity.get_record_by_pid(entity_person_data['pid'])
    assert RemoteEntitiesSearch().count() == 0

    with pytest.raises(ValidationError):
        doc = Document.create(
            data={},
            delete_pid=False, dbcommit=True, reindex=True)

    assert not Document.get_record_by_pid(doc.get('pid'))
    assert not RemoteEntity.get_record_by_pid(entity_person_data['pid'])
    assert RemoteEntitiesSearch().count() == 0
    data = deepcopy(document_data_ref)
    contrib = data.pop('contribution')
    doc = Document.create(
        data=data,
        delete_pid=False, dbcommit=False, reindex=False)
    doc.reindex()
    flush_index(DocumentsSearch.Meta.index)
    with pytest.raises(ValidationError):
        doc['contribution'] = contrib
        # remove required property
        doc.pop('type')
        doc.update(doc, commit=True, dbcommit=True, reindex=True)
    assert Document.get_record_by_pid(doc.get('pid'))
    assert not RemoteEntity.get_record_by_pid(entity_person_data['pid'])
    assert RemoteEntitiesSearch().count() == 0

    data = deepcopy(document_data_ref)
    doc.update(data, commit=True, dbcommit=False, reindex=False)
    doc.reindex()
    assert Document.get_record_by_pid(doc.get('pid'))
    assert RemoteEntity.get_record_by_pid(entity_person_data['pid'])
    assert RemoteEntitiesSearch().count() == 1

    doc.delete_from_index()
    db.session.rollback()


@mock.patch('requests.Session.get')
def test_document_linked_subject(
    mock_subjects_mef_get, app, document_data_tmp,
    mef_concept1_data, mef_concept1_es_response
):
    """Load document with MEF reference as a subject."""
    mock_subjects_mef_get.return_value = mock_response(
        json_data=mef_concept1_es_response)

    concept_pid = mef_concept1_data['idref']['pid']
    entity_uri = f'https://mef.rero.ch/api/concepts/idref/{concept_pid}'
    document_data_tmp['subjects'] = [{'entity': {'$ref': entity_uri}}]

    doc = Document.create(document_data_tmp,
                          delete_pid=True, dbcommit=True, reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    doc = Document.get_record(doc.id)

    # a "bf:Concepts" entity should be created.
    #    - Check if the entity has been created
    #    - Check if ES mapping is correct for this entity
    _, _type, _id = extract_data_from_mef_uri(entity_uri)
    entity = RemoteEntity.get_entity(_type, _id)
    assert _type in entity.get('sources')

    es_record = RemoteEntitiesSearch().get_record_by_pid(entity.pid)
    assert es_record['type'] == EntityType.TOPIC
    assert es_record[_type]['pid'] == _id

    # Check the document ES record
    #    - check if $ref linked subject is correctly dumped
    es_record = DocumentsSearch().get_record_by_pid(doc.pid)
    subject = es_record['subjects'][0]
    assert subject['entity']['primary_source'] == _type
    assert _id in subject['entity']['pids'][_type]
    assert subject['entity']['authorized_access_point_fr'] == \
        'Antienzymes'
    assert 'Inhibiteurs enzymatiques' \
           in subject['entity']['variant_access_point']

    # reset fixtures
    doc.delete_from_index()
    doc.delete()
    entity.delete()


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


def test_document_contribution_resolve_exception(es_clear, db, mef_agents_url,
                                                 document_data_ref):
    """Test document contribution resolve."""
    document_data_ref['contribution'] = [{
        '$ref': f'{mef_agents_url}/rero/XXXXXX'
    }],
    with pytest.raises(Exception):
        Document.create(
            data=document_data_ref,
            delete_pid=False,
            dbcommit=True,
            reindex=True
        )


def test_document_create_invalid_data(es_clear, db, document_data):
    """Test document contribution resolve."""
    data = deepcopy(document_data)
    n_pids = DocumentIdentifier.query.count()
    data.pop('type')
    data.pop('pid')
    with pytest.raises(Exception):
        Document.create(
            data=data,
            delete_pid=True,
            dbcommit=True,
            reindex=True
        )
    db.session.rollback()
    assert DocumentIdentifier.query.count() == n_pids


def test_document_get_links_to_me(document, export_document):
    """Test document links."""
    assert document.get_links_to_me() == {'documents': 1}
    assert document.get_links_to_me(get_pids=True) == {
        'documents': {
            'partOf': [export_document.pid]
        }
    }


def test_document_indexing(document, export_document):
    """Test document indexing."""
    # get the export_document from the es index
    s = DocumentsSearch().filter('term', pid=export_document.pid)
    assert s.count() == 1
    # get the partOf field
    record = next(s.source('partOf').scan())
    # get the titles from the host document
    parent_titles = [
        v['_text'] for v in document.dumps().get('title')
        if v.get('_text') and v.get('type') == 'bf:Title'
    ]
    assert record.partOf[0].document.title == parent_titles.pop()

    # change the title of the host document
    orig_title = document['title'][0]['mainTitle'][1]['value']
    document['title'][0]['mainTitle'][1]['value'] = 'New title'
    document.update(document, dbcommit=True, reindex=True)

    # process the bulked indexed documents
    process_bulk_queue()
    flush_index(DocumentsSearch.Meta.index)

    # get the export_document from the es index
    s = DocumentsSearch().filter('term', pid=export_document.pid)
    # get the partOf field
    record = next(s.source('partOf').scan())
    # get the titles from the host document
    parent_titles = [
        v['_text'] for v in document.dumps().get('title')
        if v.get('_text') and v.get('type') == 'bf:Title'
    ]
    assert record.partOf[0].document.title == parent_titles.pop()

    # check updated created should exists
    record = next(s.source(['_updated', '_created']).scan())
    assert record._updated
    assert record._created

    # restore initial data
    document['title'].pop(-1)
    document['title'][0]['mainTitle'][1]['value'] = orig_title
    document.update(document, dbcommit=True, reindex=True)


def test_document_replace_refs(document, mef_agents_url):
    """Test document replace refs."""
    orig = deepcopy(document)
    data = document.replace_refs()
    assert len(data.get('contribution')) == 1

    # add MEF contribution agent
    document['contribution'].append({
        'entity': {'$ref': f'{mef_agents_url}/rero/A017671081'},
        'role': ['aut']
    })

    document.update(document, dbcommit=True, reindex=True)
    flush_index(DocumentsSearch.Meta.index)
    es_doc = DocumentsSearch().get_record_by_pid(document.pid).to_dict()
    assert es_doc['contribution'][1]['entity']['type'] == EntityType.PERSON

    data = document.replace_refs()
    assert len(data.get('contribution')) == 2
    assert 'entity' in data.get('contribution')[1]
    assert data.get('contribution')[1].get('role') == ['aut']

    # Reset fixtures
    document.update(orig, dbcommit=True, reindex=True)
