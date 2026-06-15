# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API tests for indexer utilities."""

from unittest import mock

import pytest
from elasticsearch import NotFoundError

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.indexer_utils import record_to_index
from rero_ils.modules.libraries.api import LibrariesIndexer, LibrariesSearch


def test_record_indexing(app, lib_martigny):
    """Test record indexing process."""

    # TEST#1 :: Test indexing without $ref replacement
    app.config["INDEXER_REPLACE_REFS"] = False
    lib_martigny.reindex()
    LibrariesSearch.flush_and_refresh()
    record = LibrariesSearch().get_record_by_pid(lib_martigny.pid)
    assert "$ref" in record.organisation.to_dict()

    # TEST#2 :: Raise exception during indexing process
    with mock.patch(
        "rero_ils.modules.api.IlsRecordsIndexer._index_action",
        side_effect=Exception("Test!"),
    ):
        indexer = LibrariesIndexer()
        indexer.bulk_index([lib_martigny.id])
        res = indexer.process_bulk_queue()
        assert res[1] == (0, 0)

    # RESET INDEX
    app.config["INDEXER_REPLACE_REFS"] = True
    lib_martigny.reindex()
    LibrariesSearch.flush_and_refresh()


def test_record_to_index(app):
    """Test the index name value from the JSONSchema."""

    # for documents
    assert (
        record_to_index({"$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"})
        == "documents-document-v0.0.1"
    )
    assert (
        record_to_index({"$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json"})
        == "documents-document-v0.0.1"
    )

    # for mef-mef-contributions
    assert (
        record_to_index({"$schema": "https://mef.rero.ch/schemas/mef/mef-contribution-v0.0.1.json"})
        == "remote_entities-remote_entity-v0.0.1"
    )

    # for others
    assert (
        record_to_index({"$schema": "https://bib.rero.ch/schemas/organisations/organisation-v0.0.1.json"})
        == "organisations-organisation-v0.0.1"
    )


def test_get_resource_from_ES(document):
    """Test get_resource from ElasticSearch engine."""
    metadata = DocumentsSearch().get_record_by_pid("doc1")
    assert metadata
    fields = ["pid", "title"]
    metadata = DocumentsSearch().get_record_by_pid("doc1", fields=fields)
    assert all(term in metadata for term in fields)
    assert "statement" not in metadata

    with pytest.raises(NotFoundError):
        DocumentsSearch().get_record_by_pid("dummy_pid")
