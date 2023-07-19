# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Update claimed issue status."""

from logging import getLogger

from invenio_db import db

from rero_ils.modules.items.api import Item, ItemsIndexer, ItemsSearch
from rero_ils.modules.items.models import ItemIssueStatus

# revision identifiers, used by Alembic.
revision = '64a5cc96f96e'
down_revision = 'e63e5dfa2416'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')
chunck_size = 1000


def upgrade():
    """Update item issue obsolete 'claimed' status."""
    query = ItemsSearch() \
        .filter('term', issue__status='claimed') \
        .source(False)
    uuids = [hit.meta.id for hit in query.scan()]
    for idx, uuid in enumerate(uuids, 1):
        record = Item.get_record(uuid)
        LOGGER.info(f'[{idx}/{len(uuids)}] Processing Item#{record.pid} '
                    f'[{record.id}]...')
        status = ItemIssueStatus.LATE
        if record['issue'].get('received_date'):
            status = ItemIssueStatus.RECEIVED
        record['issue']['status'] = status
        record.get('issue', {}).pop('claims_count', None)
        record.update(record, commit=True)
        if idx % chunck_size == 0:  # commit DB changes every 1000 changes.
            db.session.commit()
    db.session.commit()
    _indexing_records(uuids)


def downgrade():
    """Downgrade item data model."""
    # Cannot reverse the upgrade process because we cannot determine the
    # candidates for downgrade as some issues has already states RECEIVED or
    # LATE.


def _indexing_records(record_ids):
    """Indexing some record based on record uuid."""
    if not record_ids:
        return

    LOGGER.info(f'Indexing {len(record_ids)} records ....')
    indexer = ItemsIndexer()
    chunks = [
        record_ids[x:x + chunck_size]
        for x in range(0, len(record_ids), chunck_size)
    ]
    total_indexed = 0
    for chuncked_ids in chunks:
        indexer.bulk_index(chuncked_ids)
        _, count = indexer.process_bulk_queue()
        total_indexed += count[0]
        LOGGER.info(f'{total_indexed}/{len(record_ids)} records indexed.')
