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

"""PatronType :: add unpaid subscription limit."""

from logging import getLogger

from rero_ils.modules.patron_types.api import (
    PatronType,
    PatronTypesIndexer,
    PatronTypesSearch,
)

revision = "90d857fb5c23"
down_revision = "2b0af71048a7"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Upgrade patron type records.

    We need to add the new 'unpaid_subscription' limit to each patron_type
    records that doesn't already define such a limit. The default value for
    existing records will be `False` to not generate unstable behavior.
    """
    query = (
        PatronTypesSearch()
        .exclude("exists", field="limits.unpaid_subscription")
        .source("pid")
    )
    patron_type_pids = [hit.pid for hit in query.scan()]
    ids = []
    for pid in patron_type_pids:
        record = PatronType.get_record_by_pid(pid)
        record.setdefault("limits", {}).setdefault("unpaid_subscription", False)
        record.update(record, dbcommit=True, reindex=False)
        LOGGER.info(f"  * Updated PatronType#{record.pid}")
        ids.append(record.id)
    _indexing_records(ids)
    LOGGER.info(f"TOTAL :: {len(ids)}")


def downgrade():
    """Downgrade patron type records."""
    query = (
        PatronTypesSearch()
        .filter("exists", field="limits.unpaid_subscription")
        .source("pid")
    )
    patron_type_pids = [hit.pid for hit in query.scan()]
    ids = []
    for pid in patron_type_pids:
        record = PatronType.get_record_by_pid(pid)
        del record["limits"]["unpaid_subscription"]
        record.update(record, dbcommit=True, reindex=False)
        LOGGER.info(f"  * Updated PatronType#{record.pid}")
        ids.append(record.id)
    _indexing_records(ids)
    LOGGER.info(f"TOTAL :: {len(ids)}")


def _indexing_records(record_ids):
    """Indexing some record based on record uuid."""
    if len(record_ids):
        LOGGER.info(f"Indexing {len(record_ids)} records ....")
        indexer = PatronTypesIndexer()
        indexer.bulk_index(record_ids)
        count = indexer.process_bulk_queue()
        LOGGER.info(f"{count} records indexed.")
