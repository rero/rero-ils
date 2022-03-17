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

"""Correct holdings items_count and public_items_count."""
from logging import getLogger

from elasticsearch_dsl import Document
from invenio_search import current_search_client

from rero_ils.modules.holdings.api import HoldingsSearch
from rero_ils.modules.items.api import ItemsSearch

# revision identifiers, used by Alembic.
revision = '05555c03fe49'
down_revision = 'b90f8b148948'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def upgrade():
    """Upgrade index holdings."""
    upgrade_downgrade('upgrade')


def downgrade():
    """Downgrade index holdings."""
    upgrade_downgrade('downgrade')


def upgrade_downgrade(action):
    """Upgrade or downgrade index holdings.

    Correct items_count and public_items_count for holdings of type serial.
    :param str action: upgrade or downgrade.
    """
    index = HoldingsSearch.Meta.index
    query = HoldingsSearch()\
        .filter('term', holdings_type='serial') \
        .source(['pid'])

    ids = [(h.meta.id, h.pid) for h in query.scan()]
    count = 0

    LOGGER.info(f'Indexing {len(ids)} records ....')
    for (_id, pid) in ids:
        document = Document.get(_id, index=index, using=current_search_client)
        items_count, public_items_count = get_counts(pid, action)

        document.update(items_count=items_count,
                        public_items_count=public_items_count,
                        index=index,
                        using=current_search_client,
                        refresh=True)
        count += 1
        LOGGER.info(f'{count} records indexed.')


def get_counts(pid, action):
    """Calculate items_count and public_items_count.

    :param str pid: holding pid.
    :param str action: upgrade or downgrade.
    :return: items_count and public_items_count
    """
    if action == 'upgrade':
        item_search = ItemsSearch()[0:0]\
                .filter('term', holding__pid=pid)\
                .filter('term', issue__status="received")
    else:
        item_search = ItemsSearch()[0:0]\
                .filter('term', holding__pid=pid)

    items_count = item_search.count()
    results = item_search.source([]).scan()
    public_items_count = len([res for res in results
                              if "_masked" not in res
                              or not res['_masked']])

    return items_count, public_items_count
