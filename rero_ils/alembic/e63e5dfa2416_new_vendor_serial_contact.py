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

"""New vendor serial contact."""

from logging import getLogger

# revision identifiers, used by Alembic.
from rero_ils.modules.vendors.api import Vendor, VendorsIndexer, VendorsSearch
from rero_ils.modules.vendors.models import VendorContactType

revision = 'e63e5dfa2416'
down_revision = 'add75cbcad66'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')
indexing_chunck_size = 1000


def upgrade():
    """Upgrade vendor data model."""
    uuids = [hit.meta.id for hit in VendorsSearch().source(False).scan()]
    uuids_to_reindex = []
    for uuid in uuids:
        record = Vendor.get_record(uuid)
        record.setdefault('communication_language', 'fre')
        changes = False
        if contact_info := record.pop('default_contact', None):
            contact_info['type'] = VendorContactType.DEFAULT
            record.setdefault('contacts', []).append(contact_info)
            changes = True
        if contact_info := record.pop('order_contact', None):
            contact_info['type'] = VendorContactType.ORDER
            if record.get('contacts', [{}])[0].get('city'):
                contact_info.setdefault('city', record['contacts'][0]['city'])
            record.setdefault('contacts', []).append(contact_info)
            changes = True
        if changes:
            LOGGER.info(f'* Updating vendor#{record.pid} [{uuid}]...')
            try:
                record.update(record, dbcommit=True, reindex=False)
                uuids_to_reindex.append(uuid)
            except Exception as e:
                LOGGER.error(f'Error for pid {record.pid}: {e}')


def downgrade():
    """Downgrade vendor data model."""
    uuids = [hit.meta.id for hit in VendorsSearch().source(False).scan()]
    uuids_to_reindex = []
    for uuid in uuids:
        record = Vendor.get_record(uuid)
        changes = False
        for contact in record.pop('contacts', []):
            contact_type = contact.pop('type', None)
            if contact_type == VendorContactType.DEFAULT:
                record['default_contact'] = contact
                changes = True
            if contact == VendorContactType.ORDER:
                record['order_contact'] = contact
                changes = True
        if changes:
            LOGGER.info(f'* Updating vendor#{record.pid} [{uuid}]...')
            record.update(record, dbcommit=True, reindex=False)
            uuids_to_reindex.append(uuid)
    _indexing_records(uuids_to_reindex)


def _indexing_records(record_ids):
    """Indexing some record based on record uuid."""
    if not record_ids:
        return

    LOGGER.info(f'Indexing {len(record_ids)} records ....')
    indexer = VendorsIndexer()
    chunks = [
        record_ids[x:x + indexing_chunck_size]
        for x in range(0, len(record_ids), indexing_chunck_size)
    ]
    total_indexed = 0
    for chuncked_ids in chunks:
        indexer.bulk_index(chuncked_ids)
        _, count = indexer.process_bulk_queue()
        total_indexed += count[0]
        LOGGER.info(f'{total_indexed}/{len(record_ids)} records indexed.')
