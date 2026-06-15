# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Correct holdings items_count and public_items_count."""

from logging import getLogger

from rero_ils.modules.holdings.api import Holding, HoldingsSearch

# revision identifiers, used by Alembic.
revision = "05555c03fe49"
down_revision = "b90f8b148948"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Upgrade index holdings."""
    errors = upgrade_downgrade("upgrade")
    LOGGER.info(f"upgraded to version: {revision} errors: {errors}")


def downgrade():
    """Downgrade index holdings."""
    errors = upgrade_downgrade("downgrade")
    LOGGER.info(f"downgraded to version: {down_revision} errors: {errors}")


def upgrade_downgrade(action):
    """Upgrade or downgrade index holdings.

    Correct items_count and public_items_count for holdings of type serial.
    :param str action: upgrade or downgrade.
    """
    query = HoldingsSearch().filter("term", holdings_type="serial").source(["pid"])

    ids = [(h.meta.id, h.pid) for h in query.scan()]

    LOGGER.info(f"Indexing {len(ids)} records ....")
    errors = 0
    for idx, (id, pid) in enumerate(ids):
        LOGGER.info(f"{idx} * Reindex holding: {pid}.")
        try:
            hold = Holding.get_record(id)
            hold.reindex()
        except Exception as err:
            LOGGER.error(f"{idx} * Reindex holding: {pid} {err}")
            errors += 1
    return errors
