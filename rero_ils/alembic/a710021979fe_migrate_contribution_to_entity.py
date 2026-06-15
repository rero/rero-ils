# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migrate Contribution to Entity."""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a710021979fe"
down_revision = "8145a7cdef99"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.rename_table("contribution_id", "entity_id")
    op.rename_table("contribution_metadata", "entity_metadata")


def downgrade():
    """Downgrade database."""
    op.rename_table("entity_id", "contribution_id")
    op.rename_table("entity_metadata", "contribution_metadata")
