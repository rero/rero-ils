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

"""Migrate Contribution to Entity."""

from alembic import op

# revision identifiers, used by Alembic.
revision = 'a710021979fe'
down_revision = '8145a7cdef99'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.rename_table('contribution_id', 'entity_id')
    op.rename_table('contribution_metadata', 'entity_metadata')


def downgrade():
    """Downgrade database."""
    op.rename_table('entity_id', 'contribution_id')
    op.rename_table('entity_metadata', 'contribution_metadata')
