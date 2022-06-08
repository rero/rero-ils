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

"""API tests for indexer utilities."""
import pytest
from elasticsearch import NotFoundError

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.indexer_utils import record_to_index


def test_record_to_index(app):
    """Test the index name value from the JSONSchema."""

    # for documents
    assert record_to_index({
        '$schema': 'https://bib.rero.ch/schemas/'
        'documents/document-v0.0.1.json'
    }) == ('documents-document-v0.0.1', '_doc')
    assert record_to_index({
        '$schema': 'https://bib.rero.ch/schemas/'
        'documents/document-v0.0.1.json'
    }) == ('documents-document-v0.0.1', '_doc')

    # for mef-mef-contributions
    assert record_to_index({
        '$schema': 'https://mef.rero.ch/schemas/'
        'mef/mef-contribution-v0.0.1.json'
    }) == ('contributions-contribution-v0.0.1', '_doc')

    # for others
    assert record_to_index({
        '$schema': 'https://bib.rero.ch/schemas/'
        'organisations/organisation-v0.0.1.json'
    }) == ('organisations-organisation-v0.0.1', '_doc')


def test_get_resource_from_ES(document):
    """Test get_resource from ElasticSearch engine."""
    metadata = DocumentsSearch().get_record_by_pid('doc1')
    assert metadata
    fields = ['pid', 'title']
    metadata = DocumentsSearch().get_record_by_pid('doc1', fields=fields)
    assert all(term in metadata for term in fields)
    assert 'statement' not in metadata

    with pytest.raises(NotFoundError):
        DocumentsSearch().get_record_by_pid('dummy_pid')
