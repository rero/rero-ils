# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Merging RERO-ILS branches."""

from logging import getLogger

# revision identifiers, used by Alembic.
revision = "eec683a446e5"
down_revision = ("fc45b1b998b8", "a941628259e1")
branch_labels = ()
depends_on = None


LOGGER = getLogger("alembic")


def upgrade():
    """Upgrade database."""
    LOGGER.info("Merging commit, nothing to do")


def downgrade():
    """Downgrade database."""
    LOGGER.info("Merging commit, nothing to do")
