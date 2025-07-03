# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Add keys into loan index."""

from logging import getLogger

from invenio_circulation.proxies import current_circulation

from rero_ils.modules.loans.api import LoansIndexer
from rero_ils.modules.loans.models import LoanState

revision = "a941628259e1"
down_revision = "21a994dc2beb"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")
indexing_chunck_size = 1000


def upgrade():
    """Reindex 'opened' loans to add some keys into ES index."""
    # Keep only loan without `location_pid` field (these loans are already
    # indexed with correct data)
    query = (
        current_circulation.loan_search_cls()
        .exclude("terms", state=LoanState.CONCLUDED)
        .exclude("exists", field="location_pid")
        .source("pid")
    )
    loan_uuids = [hit.meta.id for hit in query.scan()]
    _indexing_records(loan_uuids)


def downgrade():
    """Downgrade database."""


def _indexing_records(record_ids):
    """Indexing some record based on record uuid."""
    if not record_ids:
        return

    LOGGER.info(f"Indexing {len(record_ids)} records ....")
    indexer = LoansIndexer()
    chunks = [
        record_ids[x : x + indexing_chunck_size]
        for x in range(0, len(record_ids), indexing_chunck_size)
    ]
    for chuncked_ids in chunks:
        indexer.bulk_index(chuncked_ids)
        count = indexer.process_bulk_queue()
        LOGGER.info(f"{count} records indexed.")
