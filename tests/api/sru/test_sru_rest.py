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

from flask import url_for
from utils import get_xml_dict

from rero_ils.modules.documents.api import Document


def test_sru_explain(client):
    """Test sru documents rest api."""
    api_url = url_for('api_sru.documents')
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert 'sru:explainResponse' in xml_dict


def test_sru_documents(client, document_ref, entity_person_data):
    """Test sru documents rest api."""
    api_url = url_for('api_sru.documents',
                      version='1.1', operation='searchRetrieve',
                      query='al-Wajīz')
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert 'zs:searchRetrieveResponse' in xml_dict
    search_rr = xml_dict['zs:searchRetrieveResponse']
    assert search_rr.get('zs:echoedSearchRetrieveRequest') == {
        'zs:maximumRecords': '100',
        'zs:query': 'al-Wajīz',
        'zs:query_es': 'al-Wajīz',
        'zs:recordPacking': 'XML',
        'zs:recordSchema': 'info:sru/schema/1/marcxml-v1.1-light',
        'zs:resultSetTTL': '0',
        'zs:startRecord': '1'
    }
    assert search_rr.get('zs:numberOfRecords') == str(Document.count())


def test_sru_documents_items(client, document_sion_items):
    """Test sru documents with items."""
    api_url = url_for('api_sru.documents',
                      version='1.1', operation='searchRetrieve',
                      query='"La reine Berthe et son fils"')
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert 'zs:searchRetrieveResponse' in xml_dict
    ech_srr = xml_dict['zs:searchRetrieveResponse'][
        'zs:echoedSearchRetrieveRequest']
    assert ech_srr['zs:query'] == '"La reine Berthe et son fils"'
    assert ech_srr['zs:query_es'] == '"La reine Berthe et son fils"'

    api_url = url_for('api_sru.documents',
                      version='1.1', operation='searchRetrieve',
                      query='"La reine Berthe et son fils"',
                      format='marcxml')
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert 'zs:searchRetrieveResponse' in xml_dict
    ech_srr = xml_dict['zs:searchRetrieveResponse'][
        'zs:echoedSearchRetrieveRequest']
    assert ech_srr['zs:query'] == '"La reine Berthe et son fils"'
    assert ech_srr['zs:query_es'] == '"La reine Berthe et son fils"'

    api_url = url_for('api_sru.documents',
                      version='1.1', operation='searchRetrieve',
                      query='dc.title="La reine Berthe et son fils"',
                      format='dc')
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert 'searchRetrieveResponse' in xml_dict
    ech_srr = xml_dict['searchRetrieveResponse']['echoedSearchRetrieveRequest']
    assert ech_srr['query'] == 'dc.title="La reine Berthe et son fils"'
    assert ech_srr['query_es'] == 'title.\\*:' \
                                  '"La reine Berthe et son fils"'


def test_sru_documents_diagnostics(client):
    """Test sru documents diagnostics."""
    api_url = url_for('api_sru.documents',
                      version='1.1', operation='searchRetrieve',
                      query='(((')
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert 'srw:searchRetrieveResponse' in xml_dict
    assert xml_dict['srw:searchRetrieveResponse'][
        'diag:diagnostics']['diag:message'] == 'Malformed Query'
