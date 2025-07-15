# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2020 UCLouvain
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


"""holdings affiliated to libraries."""

from logging import getLogger

from rero_ils.modules.organisations.api import Organisation, OrganisationsSearch

# revision identifiers, used by Alembic.
revision = "fc45b1b998b8"
down_revision = "74ab9da9f078"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Upgrade organisations online_harvested_source to list."""
    query = OrganisationsSearch().filter("exists", field="online_harvested_source")
    LOGGER.info(f"Update Organisations: {query.count()}")
    for idx, hit in enumerate(query.source("pid").scan()):
        org = Organisation.get_record_by_pid(hit.pid)
        org["online_harvested_source"] = [org["online_harvested_source"]]
        LOGGER.info(f"{idx:<3} org: {org.pid} -> {org['online_harvested_source']}")
        org.update(data=org, dbcommit=True, reindex=True)


def downgrade():
    """Downgrade organisations online_harvested_source to string."""
    query = OrganisationsSearch().filter("exists", field="online_harvested_source")
    LOGGER.info(f"Downgrad Organisations: {query.count()}")
    for idx, hit in enumerate(query.source("pid").scan()):
        org = Organisation.get_record_by_pid(hit.pid)
        org["online_harvested_source"] = org["online_harvested_source"][0]
        LOGGER.info(f"{idx:<3} org: {org.pid} -> {org['online_harvested_source']}")
        org.update(data=org, dbcommit=True, reindex=True)
