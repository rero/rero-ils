# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""reindex items with invalid EAN."""

from logging import getLogger

from elasticsearch_dsl.query import Q

from rero_ils.modules.documents.api import DocumentsIndexer, DocumentsSearch

# revision identifiers, used by Alembic.
revision = "8145a7cdef99"
down_revision = "5f0b086e4b82"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")
indexing_chunck_size = 1000


def upgrade():
    """Upgrade database."""
    query = (
        DocumentsSearch()
        .filter(
            "nested",
            path="nested_identifiers",
            query=Q(
                "bool",
                must=[
                    Q("term", nested_identifiers__type="bf:Ean"),
                    ~Q("exists", field="nested_identifiers.value"),
                ],
            ),
        )
        .source(False)
    )
    uuids = [hit.meta.id for hit in query.scan()]
    _indexing_records(uuids)


def downgrade():
    """Downgrade database."""


def _indexing_records(record_ids):
    """Indexing some record based on record uuid."""
    if not record_ids:
        return

    LOGGER.info(f"Indexing {len(record_ids)} records ....")
    indexer = DocumentsIndexer()
    chunks = [record_ids[x : x + indexing_chunck_size] for x in range(0, len(record_ids), indexing_chunck_size)]
    for chuncked_ids in chunks:
        indexer.bulk_index(chuncked_ids)
        _, (indexer_count, error_count) = indexer.process_bulk_queue()
        LOGGER.info(f"{indexer_count} records indexed, {error_count} errors")
