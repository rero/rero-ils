# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
# Copyright (C) 2023 UCLouvain
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

"""Migration ill pickup."""

from logging import getLogger

from rero_ils.modules.locations.api import Location, LocationsSearch

revision = 'e3eb396b39bb'
down_revision = '8145a7cdef99'
branch_labels = ()
depends_on = None

LOGGER = getLogger('alembic')


def upgrade():
    """Upgrade locations records.

    Assign ill pickup on locations that are pickup.
    """
    query = LocationsSearch() \
        .filter('term', is_pickup=True) \
        .source(['pid'])
    hits = list(query.scan())
    for hit in hits:
        location = Location.get_record_by_pid(hit.pid)
        location['is_ill_pickup'] = True
        location['ill_pickup_name'] = location['pickup_name']
        location.update(location, dbcommit=True, reindex=True)
        LOGGER.info(f'  * Upgrade location#{location.pid}')
    LOGGER.info(f'TOTAL :: {len(hits)}')


def downgrade():
    """Downgrade database."""
    # Nothing to do
