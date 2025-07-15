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

"""Loan :: add checkout location pid to current ON_LOAN laons."""

from logging import getLogger

from elasticsearch_dsl import Q
from invenio_circulation.proxies import current_circulation

from rero_ils.modules.loans.api import Loan, LoansIndexer
from rero_ils.modules.loans.models import LoanState

# revision identifiers, used by Alembic.
revision = "54134957af7d"
down_revision = "90d857fb5c23"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")
indexing_chunck_size = 1000


def upgrade():
    """Upgrade ON_LOAN records.

    For all ON_LOAN records, we will add a new `checkout_location_pid` field
    used to calculate fees based on checkout library.
    """
    query = (
        current_circulation.loan_search_cls()
        .filter("term", state=LoanState.ITEM_ON_LOAN)
        .filter("bool", must_not=[Q("exists", field="checkout_location_pid")])
        .source(["pid", "transaction_location_pid"])
    )
    loans_hits = list(query.scan())
    ids = []
    for hit in loans_hits:
        loan = Loan.get_record_by_pid(hit.pid)
        loan["checkout_location_pid"] = hit.transaction_location_pid
        loan.update(loan, dbcommit=True, reindex=False)
        LOGGER.info(f"  * Upgrade loan#{loan.pid}")
        ids.append(loan.id)
    _indexing_records(ids)
    LOGGER.info(f"TOTAL :: {len(ids)}")


def downgrade():
    """Downgrade Loan records removing `checkout_location_pid` field."""
    query = (
        current_circulation.loan_search_cls()
        .filter("exists", field="checkout_location_pid")
        .source("pid")
    )
    loans_hits = list(query.scan())
    ids = []
    for hit in loans_hits:
        loan = Loan.get_record_by_pid(hit.pid)
        del loan["checkout_location_pid"]
        loan.update(loan, dbcommit=True, reindex=False)
        LOGGER.info(f"  * Downgrade loan#{loan.pid}")
        ids.append(loan.id)
    _indexing_records(ids)
    LOGGER.info(f"TOTAL :: {len(ids)}")


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
