# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""cipo request duration field creation."""

from logging import getLogger

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy

# revision identifiers, used by Alembic.
revision = "cc7ffbe1e078"
down_revision = "9e3145d88e64"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Update circulation policy records."""
    query = CircPoliciesSearch().filter("term", allow_requests=True).source(["pid"]).scan()
    for hit in query:
        cipo = CircPolicy.get_record_by_pid(hit.pid)
        cipo["pickup_hold_duration"] = 10  # default value is 10 days
        cipo.update(cipo, dbcommit=True, reindex=True)
        LOGGER.info(f"  * Updated cipo#{cipo.pid}")
    CircPoliciesSearch.flush_and_refresh()
    LOGGER.info(f"upgrade to {revision}")


def downgrade():
    """Reset circulation policy records."""
    query = CircPoliciesSearch().filter("exists", field="pickup_hold_duration").source(["pid"]).scan()
    for hit in query:
        cipo = CircPolicy.get_record_by_pid(hit.pid)
        del cipo["pickup_hold_duration"]
        cipo.update(cipo, dbcommit=True, reindex=True)
        LOGGER.info(f"  * Updated cipo#{cipo.pid}")
    CircPoliciesSearch.flush_and_refresh()
    LOGGER.info(f"downgrade to revision {down_revision}")
