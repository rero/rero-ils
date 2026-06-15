# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration ill pickup."""

from logging import getLogger

from rero_ils.modules.locations.api import Location, LocationsSearch

revision = "e3eb396b39bb"
down_revision = "8145a7cdef99"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Upgrade locations records.

    Assign ill pickup on locations that are pickup.
    """
    query = LocationsSearch().filter("term", is_pickup=True).source(["pid"])
    hits = list(query.scan())
    for hit in hits:
        location = Location.get_record_by_pid(hit.pid)
        location["is_ill_pickup"] = True
        location["ill_pickup_name"] = location["pickup_name"]
        location.update(location, dbcommit=True, reindex=True)
        LOGGER.info(f"  * Upgrade location#{location.pid}")
    LOGGER.info(f"TOTAL :: {len(hits)}")


def downgrade():
    """Downgrade database."""
    # Nothing to do
