# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Delete expired items temporary locations."""

from logging import getLogger

from rero_ils.modules.items.api import Item, ItemsSearch

revision = 'ce4923ba5286'
down_revision = '05555c03fe49'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def index_items_with_temporary_location():
    """Index items with temporary location."""
    query = ItemsSearch() \
        .filter('exists', field='temporary_location').source(['pid'])
    ids = [(hit.meta.id, hit.pid) for hit in query.scan()]
    errors = 0
    for idx, (id, pid) in enumerate(ids):
        LOGGER.info(f'{idx} * Reindex item: {pid}')
        try:
            item = Item.get_record(id)
            item.reindex()
        except Exception as err:
            LOGGER.error(f'{idx} * Reindex item: {pid} {err}')
            errors += 1
    return errors


def upgrade():
    """Index items with temporary location."""
    errors = index_items_with_temporary_location()
    LOGGER.info(f'upgraded to version: {revision} errors: {errors}')


def downgrade():
    """Index items with temporary location."""
    errors = index_items_with_temporary_location()
    LOGGER.info(f'downgraded to version: {down_revision} errors: {errors}')
