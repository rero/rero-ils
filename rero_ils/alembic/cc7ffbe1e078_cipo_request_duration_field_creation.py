# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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
    query = (
        CircPoliciesSearch().filter("term", allow_requests=True).source(["pid"]).scan()
    )
    for hit in query:
        cipo = CircPolicy.get_record_by_pid(hit.pid)
        cipo["pickup_hold_duration"] = 10  # default value is 10 days
        cipo.update(cipo, dbcommit=True, reindex=True)
        LOGGER.info(f"  * Updated cipo#{cipo.pid}")
    CircPoliciesSearch.flush_and_refresh()
    LOGGER.info(f"upgrade to {revision}")


def downgrade():
    """Reset circulation policy records."""
    query = (
        CircPoliciesSearch()
        .filter("exists", field="pickup_hold_duration")
        .source(["pid"])
        .scan()
    )
    for hit in query:
        cipo = CircPolicy.get_record_by_pid(hit.pid)
        del cipo["pickup_hold_duration"]
        cipo.update(cipo, dbcommit=True, reindex=True)
        LOGGER.info(f"  * Updated cipo#{cipo.pid}")
    CircPoliciesSearch.flush_and_refresh()
    LOGGER.info(f"downgrade to revision {down_revision}")
