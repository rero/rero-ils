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

"""Merging RERO-ILS branches."""

from logging import getLogger

# revision identifiers, used by Alembic.
revision = 'eec683a446e5'
down_revision = ('fc45b1b998b8', 'a941628259e1')
branch_labels = ()
depends_on = None


LOGGER = getLogger('alembic')


def upgrade():
    """Upgrade database."""
    LOGGER.info("Merging commit, nothing to do")


def downgrade():
    """Downgrade database."""
    LOGGER.info("Merging commit, nothing to do")
