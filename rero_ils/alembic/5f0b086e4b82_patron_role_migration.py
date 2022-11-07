# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Patron role migration."""

from logging import getLogger

from rero_ils.modules.patrons.api import Patron, PatronsIndexer, PatronsSearch
from rero_ils.modules.users.models import UserRole

# revision identifiers, used by Alembic.
revision = '5f0b086e4b82'
down_revision = 'eec683a446e5'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')
indexing_chunck_size = 100


def upgrade():
    """Upgrade database."""

    def get_new_roles(roles):
        if 'system_librarian' in roles:
            return [UserRole.FULL_PERMISSIONS]
        elif 'librarian' in roles:
            return [
                UserRole.PROFESSIONAL_READ_ONLY,
                UserRole.ACQUISITION_MANAGER,
                UserRole.CATALOG_MANAGER,
                UserRole.CIRCULATION_MANAGER,
                UserRole.USER_MANAGER
            ]

    query = PatronsSearch()\
        .filter('terms', roles=['librarian', 'system_librarian'])\
        .source(False)
    patron_uuids = []

    for hit in query.scan():
        patron = Patron.get_record(hit.meta.id)
        original_roles = patron.get('roles')
        migrated_roles = get_new_roles(original_roles)
        LOGGER.info(f'* Updating ptrn#{patron.pid} [{patron.formatted_name}]')
        LOGGER.info(f'\t - Original roles are : [{original_roles}]')
        LOGGER.info(f'\t - New roles are : [{migrated_roles}]')
        patron['roles'] = migrated_roles
        patron.update(patron, dbcommit=True, reindex=False)
        patron_uuids.append(hit.meta.id)

    _indexing_records(patron_uuids)


def downgrade():
    """Downgrade database."""

    def get_original_roles(roles):
        if UserRole.FULL_PERMISSIONS in roles:
            return ['system_librarian']
        elif any(role in UserRole.LIBRARIAN_ROLES for role in roles):
            return ['librarian']

    query = PatronsSearch()\
        .filter('terms', roles=UserRole.PROFESSIONAL_ROLES)\
        .source(False)
    patron_uuids = []

    for hit in query.scan():
        patron = Patron.get_record(hit.meta.id)
        current_roles = patron.get('roles')
        original_roles = get_original_roles(current_roles)
        LOGGER.info(f'* Updating ptrn#{patron.pid} [{patron.formatted_name}]')
        LOGGER.info(f'\t - Current roles are : {current_roles}')
        LOGGER.info(f'\t - Original roles are : {original_roles}')
        patron['roles'] = original_roles
        patron.update(patron, dbcommit=True, reindex=False)
        patron_uuids.append(hit.meta.id)

    _indexing_records(patron_uuids)


def _indexing_records(record_ids):
    """Indexing some record based on record uuid."""
    if not record_ids:
        return

    LOGGER.info(f'Indexing {len(record_ids)} records ....')
    indexer = PatronsIndexer()
    chunks = [
        record_ids[x:x + indexing_chunck_size]
        for x in range(0, len(record_ids), indexing_chunck_size)
    ]
    for chuncked_ids in chunks:
        indexer.bulk_index(chuncked_ids)
        count = indexer.process_bulk_queue()
        LOGGER.info(f'{count} records indexed.')
