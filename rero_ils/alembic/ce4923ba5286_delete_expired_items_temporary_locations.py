# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Delete expired items temporary locations."""

from logging import getLogger

from rero_ils.modules.items.api import Item, ItemsSearch

revision = "ce4923ba5286"
down_revision = "05555c03fe49"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def index_items_with_temporary_location():
    """Index items with temporary location."""
    query = ItemsSearch().filter("exists", field="temporary_location").source(["pid"])
    ids = [(hit.meta.id, hit.pid) for hit in query.scan()]
    errors = 0
    for idx, (id, pid) in enumerate(ids):
        LOGGER.info(f"{idx} * Reindex item: {pid}")
        try:
            item = Item.get_record(id)
            item.reindex()
        except Exception as err:
            LOGGER.error(f"{idx} * Reindex item: {pid} {err}")
            errors += 1
    return errors


def upgrade():
    """Index items with temporary location."""
    errors = index_items_with_temporary_location()
    LOGGER.info(f"upgraded to version: {revision} errors: {errors}")


def downgrade():
    """Index items with temporary location."""
    errors = index_items_with_temporary_location()
    LOGGER.info(f"downgraded to version: {down_revision} errors: {errors}")
