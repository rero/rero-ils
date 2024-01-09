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

"""Tests REST API documents."""

# import json
# from utils import get_json, to_relative_url

import mock
import requests
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, clean_text, get_json, \
    mock_response, to_relative_url

from rero_ils.modules.documents.api import Document
from rero_ils.modules.imports.api import LoCImport


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_get(client, document):
    """Test record retrieval."""
    def clean_es_metadata(metadata):
        """Clean contribution from authorized_access_point_"""
        # Contributions, subject and genreForm are i18n indexed field, so it's
        # too complicated to compare it from original record. Just take the
        # data from original record ... not best, but not real alternatives.
        if contribution := document.get('contribution'):
            metadata['contribution'] = contribution
        if subjects := document.get('subjects'):
            metadata['subjects'] = subjects
        if genreForms := document.get('genreForm'):
            metadata['genreForm'] = genreForms

        # REMOVE DYNAMICALLY ADDED ES KEYS (see indexer.py:IndexerDumper)
        metadata.pop('sort_date_new', None)
        metadata.pop('sort_date_old', None)
        metadata.pop('sort_title', None)
        metadata.pop('isbn', None)
        metadata.pop('issn', None)
        metadata.pop('nested_identifiers', None)
        metadata.pop('identifiedBy', None)
        return metadata

    item_url = url_for('invenio_records_rest.doc_item', pid_value='doc1')
    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{document.revision_id}"'
    data = get_json(res)
    # DEV NOTES : Why removing `identifiedBy` key
    #   During the ES enrichment process, we complete the original identifiers
    #   with alternate identifiers. So comparing ES data identifiers, to
    #   original data identifiers doesn't make sense.
    document_data = document.dumps()
    document_data.pop('identifiedBy', None)
    assert document_data == clean_es_metadata(data['metadata'])

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    res_content = get_json(res)
    res_content.get('metadata', {}).pop('identifiedBy', None)
    assert data == res_content
    document_data = document.dumps()
    document_data.pop('identifiedBy', None)
    assert document_data == clean_es_metadata(data['metadata'])

    list_url = url_for('invenio_records_rest.doc_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    data_clean = clean_es_metadata(data['hits']['hits'][0]['metadata'])
    document = document.replace_refs().dumps()
    document.pop('identifiedBy', None)
    assert document == data_clean

    list_url = url_for('invenio_records_rest.doc_list', q="Vincent Berthe")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_imports_get_config(client, librarian_martigny):
    """Get the configuration for the external import services."""
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url_for('api_import.get_config'))
    assert res.status_code == 200
    data = get_json(res)
    assert data
    assert all('weight' in source for source in data)


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_bnf_ean(mock_get, client, bnf_ean_any_123,
                                  bnf_ean_any_9782070541270,
                                  bnf_ean_any_9782072862014,
                                  bnf_anywhere_all_peter,
                                  bnf_recordid_all_FRBNF370903960000006):
    """Test document import from bnf."""

    mock_get.return_value = mock_response(
        content=bnf_ean_any_123
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='ean:any:123',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=bnf_ean_any_9782070541270
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='ean:any:9782070541270',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    assert data['pid'] == 'FRBNF370903960000006'
    assert Document.create(data)

    mock_get.return_value = mock_response(
        content=bnf_ean_any_9782072862014
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='ean:any:9782072862014',
        no_cache=1
    ))
    assert res.status_code == 200
    res_j = get_json(res)
    data = res_j.get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    assert Document.create(data)
    marc21_link = res_j.get('hits').get('hits')[0].get('links').get('marc21')

    res = client.get(marc21_link)
    data = get_json(res)
    assert data[0][0] == 'leader'

    res = client.get(url_for(
        'api_imports.import_bnf',
        q='',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'remote_total': 0,
            'total': 0
        }
    }

    mock_get.return_value = mock_response(
        content=bnf_anywhere_all_peter
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='peter',
        no_cache=1
    ))
    assert res.status_code == 200
    unfiltered_total = get_json(res)['hits']['remote_total']
    assert get_json(res)

    res = client.get(url_for(
        'api_imports.import_bnf',
        q='peter',
        year=2000,
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_bnf',
        q='peter',
        author='Peter Owen',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_bnf',
        q='peter',
        document_type='docmaintype_book',
        document_subtype='docsubtype_other_book',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    mock_get.return_value = mock_response(
        content=bnf_recordid_all_FRBNF370903960000006
    )
    res = client.get(url_for(
        'api_imports.import_bnf_record',
        id='FRBNF370903960000006',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('identifiedBy')

    res = client.get(url_for(
        'api_imports.import_bnf_record',
        id='FRBNF370903960000006',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('ui_title_text')

    res = client.get(url_for(
        'api_imports.import_bnf_record',
        id='FRBNF370903960000006',
        format='marc'
    ))
    assert res.status_code == 200
    assert get_json(res)[1][1] == 'FRBNF370903960000006'


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_loc_isbn(mock_get, client, loc_isbn_all_123,
                                   loc_isbn_all_9781604689808,
                                   loc_isbn_all_9780821417478,
                                   loc_anywhere_all_samuelson,
                                   loc_recordid_all_2014043016):
    """Test document import from LoC."""

    mock_get.return_value = mock_response(
        content=loc_isbn_all_123
    )
    res = client.get(url_for(
        'api_imports.import_loc',
        q='isbn:all:123',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=loc_isbn_all_9781604689808
    )
    res = client.get(url_for(
        'api_imports.import_loc',
        q='isbn:all:9781604689808',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    assert data['pid'] == '2018032710'
    assert Document.create(data)

    mock_get.return_value = mock_response(
        content=loc_isbn_all_9780821417478
    )
    res = client.get(url_for(
        'api_imports.import_loc',
        q='isbn:all:9780821417478',
        no_cache=1
    ))
    assert res.status_code == 200
    res_j = get_json(res)
    data = res_j.get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    assert Document.create(data)
    marc21_link = res_j.get('hits').get('hits')[0].get('links').get('marc21')

    res = client.get(marc21_link)
    data = get_json(res)
    assert data[0][0] == 'leader'

    res = client.get(url_for(
        'api_imports.import_loc',
        q='',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'remote_total': 0,
            'total': 0
        }
    }

    mock_get.return_value = mock_response(
        content=loc_anywhere_all_samuelson
    )
    res = client.get(url_for(
        'api_imports.import_loc',
        q='samuelson',
        no_cache=1
    ))
    assert res.status_code == 200
    unfiltered_total = get_json(res)['hits']['remote_total']
    assert get_json(res)

    res = client.get(url_for(
        'api_imports.import_loc',
        q='samuelson',
        year=2019,
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_loc',
        q='samuelson',
        author='Samuelson, Paul',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_loc',
        q='samuelson',
        document_type='docmaintype_book',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    mock_get.return_value = mock_response(
        content=loc_recordid_all_2014043016
    )
    res = client.get(url_for(
        'api_imports.import_loc_record',
        id='2014043016',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('identifiedBy')

    res = client.get(url_for(
        'api_imports.import_loc_record',
        id='2014043016',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('ui_title_text')


@mock.patch('requests.get')
def test_documents_import_loc_missing_id(mock_get, client, loc_without_010):
    """Test document import from LoC."""

    mock_get.return_value = mock_response(
        content=loc_without_010
    )
    results, status_code = LoCImport().search_records(
        what='test',
        relation='all',
        where='anywhere',
        max_results=100,
        no_cache=True
    )
    assert status_code == 200
    assert results['hits']['total']['value'] == 9
    assert len(results['hits']['hits']) == 9


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_dnb_isbn(mock_get, client, dnb_isbn_123,
                                   dnb_isbn_9783862729852,
                                   dnb_isbn_3858818526,
                                   dnb_samuelson,
                                   dnb_recordid_1214325203):
    """Test document import from DNB."""

    mock_get.return_value = mock_response(
        content=dnb_isbn_123
    )
    res = client.get(url_for(
        'api_imports.import_dnb',
        q='123',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=dnb_isbn_3858818526
    )
    res = client.get(url_for(
        'api_imports.import_dnb',
        q='3858818526',
        no_cache=1
    ))
    assert res.status_code == 200
    res_j = get_json(res)
    data = res_j.get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    data = clean_text(data)
    assert Document.create(data)
    marc21_link = res_j.get('hits').get('hits')[0].get('links').get('marc21')

    res = client.get(marc21_link)
    data = get_json(res)
    assert data[0][0] == 'leader'

    res = client.get(url_for(
        'api_imports.import_dnb',
        q='',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'remote_total': 0,
            'total': 0
        }
    }

    mock_get.return_value = mock_response(
        content=dnb_samuelson
    )
    res = client.get(url_for(
        'api_imports.import_dnb',
        q='samuelson, paul',
        no_cache=1
    ))
    assert res.status_code == 200
    unfiltered_total = get_json(res)['hits']['remote_total']
    assert get_json(res)

    res = client.get(url_for(
        'api_imports.import_dnb',
        q='samuelson, paul',
        year=2019
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_dnb',
        q='samuelson, paul',
        author='Samuelson, Paul A.'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_dnb',
        q='samuelson, paul',
        document_type='docmaintype_book'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    mock_get.return_value = mock_response(
        content=dnb_recordid_1214325203
    )
    res = client.get(url_for(
        'api_imports.import_dnb_record',
        id='1214325203',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('identifiedBy')


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_slsp_isbn(mock_get, client, slsp_anywhere_123,
                                    slsp_isbn_9782296076648,
                                    slsp_isbn_3908497272,
                                    slsp_samuelson,
                                    slsp_recordid_9910137):
    """Test document import from slsp."""

    mock_get.return_value = mock_response(
        content=slsp_anywhere_123
    )
    res = client.get(url_for(
        'api_imports.import_slsp',
        q='123',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=slsp_isbn_9782296076648
    )
    res = client.get(url_for(
        'api_imports.import_slsp',
        q='isbn:all:9782296076648',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    assert data['pid'] == '991079993319705501'
    assert Document.create(data)

    mock_get.return_value = mock_response(
        content=slsp_isbn_3908497272
    )
    res = client.get(url_for(
        'api_imports.import_slsp',
        q='isbn:all:3908497272',
        no_cache=1
    ))
    assert res.status_code == 200
    res_j = get_json(res)
    data = res_j.get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    assert Document.create(data)
    marc21_link = res_j.get('hits').get('hits')[0].get('links').get('marc21')

    res = client.get(marc21_link)
    data = get_json(res)
    assert data[0][0] == 'leader'

    res = client.get(url_for(
        'api_imports.import_slsp',
        q='',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'remote_total': 0,
            'total': 0
        }
    }

    mock_get.return_value = mock_response(
        content=slsp_samuelson
    )
    res = client.get(url_for(
        'api_imports.import_slsp',
        q='samuelson',
        no_cache=1
    ))
    assert res.status_code == 200
    unfiltered_total = get_json(res)['hits']['remote_total']
    assert get_json(res)

    res = client.get(url_for(
        'api_imports.import_slsp',
        q='samuelson',
        year=2019,
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_slsp',
        q='samuelson',
        author='samuelson',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_slsp',
        q='samuelson',
        document_type='docmaintype_book',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    mock_get.return_value = mock_response(
        content=slsp_recordid_9910137
    )
    res = client.get(url_for(
        'api_imports.import_slsp_record',
        id='recordid:all:991013724759705501',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('identifiedBy')

    res = client.get(url_for(
        'api_imports.import_slsp_record',
        id='recordid:all:991013724759705501',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('ui_title_text')


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_ugent_isbn(mock_get, client, ugent_anywhere_123,
                                     ugent_isbn_9781108422925,
                                     ugent_book_without_26X,
                                     ugent_isbn_9780415773867,
                                     ugent_samuelson,
                                     ugent_recordid_001247835):
    """Test document import from ugent."""

    mock_get.return_value = mock_response(
        content=ugent_anywhere_123
    )
    res = client.get(url_for(
        'api_imports.import_ugent',
        q='123',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=ugent_isbn_9781108422925
    )
    res = client.get(url_for(
        'api_imports.import_ugent',
        q='isbn:all:9781108422925',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    assert data['pid'] == '002487518'
    assert Document.create(data)

    mock_get.return_value = mock_response(
        content=ugent_book_without_26X
    )
    res = client.get(url_for(
        'api_imports.import_ugent',
        q='isbn:all:9782717725650',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    assert data['pid'] == '002762516'
    assert Document.create(data)

    res = client.get(url_for(
        'api_imports.import_ugent',
        q='',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'remote_total': 0,
            'total': 0
        }
    }

    mock_get.return_value = mock_response(
        content=ugent_samuelson
    )
    res = client.get(url_for(
        'api_imports.import_ugent',
        q='samuelson',
        no_cache=1
    ))
    assert res.status_code == 200
    unfiltered_total = get_json(res)['hits']['remote_total']
    assert get_json(res)

    res = client.get(url_for(
        'api_imports.import_ugent',
        q='samuelson',
        year=2019,
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_ugent',
        q='samuelson',
        author='samuelson',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    mock_get.return_value = mock_response(
        content=ugent_recordid_001247835
    )
    res = client.get(url_for(
        'api_imports.import_ugent_record',
        id='recordid:all:001247835',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('identifiedBy')


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_kul_isbn(mock_get, client, kul_anywhere_123,
                                   kul_isbn_9782265089419,
                                   kul_book_without_26X,
                                   kul_isbn_2804600068,
                                   kul_samuelson,
                                   kul_recordid_9992876296301471):
    """Test document import from kul."""

    mock_get.return_value = mock_response(
        content=kul_anywhere_123
    )
    res = client.get(url_for(
        'api_imports.import_kul',
        q='123',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=kul_isbn_9782265089419
    )
    res = client.get(url_for(
        'api_imports.import_kul',
        q='isbn:all:9782265089419',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    assert data['pid'] == '9983115060101471'

    mock_get.return_value = mock_response(
        content=kul_isbn_2804600068
    )
    res = client.get(url_for(
        'api_imports.import_kul',
        q='isbn:all:2804600068',
        no_cache=1
    ))
    assert res.status_code == 200
    res_j = get_json(res)
    data = res_j.get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    assert Document.create(data)
    marc21_link = res_j.get('hits').get('hits')[0].get('links').get('marc21')

    res = client.get(marc21_link)
    data = get_json(res)
    assert data[0][0] == 'leader'

    res = client.get(url_for(
        'api_imports.import_kul',
        q='',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'remote_total': 0,
            'total': 0
        }
    }

    mock_get.return_value = mock_response(
        content=kul_samuelson
    )
    res = client.get(url_for(
        'api_imports.import_kul',
        q='samuelson',
        no_cache=1
    ))
    assert res.status_code == 200
    unfiltered_total = get_json(res)['hits']['remote_total']
    assert get_json(res)

    res = client.get(url_for(
        'api_imports.import_kul',
        q='samuelson',
        year=2019,
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_kul',
        q='samuelson',
        author='samuelson',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    res = client.get(url_for(
        'api_imports.import_kul',
        q='samuelson',
        document_type='docmaintype_book',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res)['hits']['total'] < unfiltered_total

    mock_get.return_value = mock_response(
        content=kul_recordid_9992876296301471
    )
    res = client.get(url_for(
        'api_imports.import_kul_record',
        id='recordid:all:9992876296301471',
        no_cache=1
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('identifiedBy')

    res = client.get(url_for(
        'api_imports.import_kul_record',
        id='recordid:all:9992876296301471',
        format='rerojson'
    ))
    assert res.status_code == 200
    assert get_json(res).get('metadata', {}).get('ui_title_text')


@mock.patch('requests.get')
@mock.patch('rero_ils.permissions.login_and_librarian', mock.MagicMock())
def test_documents_import_bnf_errors(mock_get, client):
    """Test document import from bnf."""

    mock_get.return_value = mock_response(
        content=b''
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='ean:any',
        no_cache=1
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    mock_get.return_value = mock_response(
        content=b'',
        status=429
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='ean:any:123',
        no_cache=1
    ))
    assert res.status_code == 429
    data = get_json(res)
    assert data.get('errors')

    err_msg = 'error'
    err_code = 555
    error = requests.exceptions.HTTPError(err_msg)
    error.response = mock.MagicMock()
    error.response.status_code = err_code
    error.response.content = 'Error Code'
    mock_get.return_value = mock_response(
        content=b'',
        status=555,
        raise_for_status=error
    )
    res = client.get(url_for(
        'api_imports.import_bnf',
        q='ean:any:123',
        no_cache=1
    ))
    data = get_json(res)
    assert res.status_code == err_code
    assert data['errors']['message'] == err_msg
