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
from mock import mock
from utils import flush_index

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.indexer_utils import record_to_index
from rero_ils.modules.libraries.api import LibrariesIndexer, LibrariesSearch


def test_record_indexing(app, lib_martigny):
    """Test record indexing process."""

    # TEST#1 :: Test indexing without $ref replacement
    app.config['INDEXER_REPLACE_REFS'] = False
    lib_martigny.reindex()
    flush_index(LibrariesSearch.Meta.index)
    record = LibrariesSearch().get_record_by_pid(lib_martigny.pid)
    assert '$ref' in record.organisation.to_dict()

    # TEST#2 :: Raise exception during indexing process
    with mock.patch(
        'rero_ils.modules.api.IlsRecordsIndexer._index_action',
        side_effect=Exception('Test!')
    ):
        indexer = LibrariesIndexer()
        indexer.bulk_index([lib_martigny.id])
        res = indexer.process_bulk_queue()
        assert res[1] == (0, 0)

    # RESET INDEX
    app.config['INDEXER_REPLACE_REFS'] = True
    lib_martigny.reindex()
    flush_index(LibrariesSearch.Meta.index)


def test_record_to_index(app):
    """Test the index name value from the JSONSchema."""

    # for documents
    assert record_to_index({
        '$schema': 'https://bib.rero.ch/schemas/'
        'documents/document-v0.0.1.json'
    }) == 'documents-document-v0.0.1'
    assert record_to_index({
        '$schema': 'https://bib.rero.ch/schemas/'
        'documents/document-v0.0.1.json'
    }) == 'documents-document-v0.0.1'

    # for mef-mef-contributions
    assert record_to_index({
        '$schema': 'https://mef.rero.ch/schemas/'
        'mef/mef-contribution-v0.0.1.json'
    }) == 'remote_entities-remote_entity-v0.0.1'

    # for others
    assert record_to_index({
        '$schema': 'https://bib.rero.ch/schemas/'
        'organisations/organisation-v0.0.1.json'
    }) == 'organisations-organisation-v0.0.1'


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
