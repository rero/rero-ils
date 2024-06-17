# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""update patron communication channels."""

from logging import getLogger

from elasticsearch_dsl import Q
from invenio_db import db

from rero_ils.modules.patrons.api import Patron, PatronsIndexer, PatronsSearch
from rero_ils.modules.patrons.models import CommunicationChannel

# revision identifiers, used by Alembic.
revision = "74ab9da9f078"
down_revision = "0387b753585f"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")


def upgrade():
    """Fix incorrectly set patron communication channels."""
    query = (
        PatronsSearch()
        .filter("term", patron__communication_channel=CommunicationChannel.EMAIL)
        .filter(
            "bool",
            must_not=[Q("exists", field="patron.additional_communication_email")],
        )
        .filter("bool", must_not=[Q("exists", field="email")])
        .source(includes="pid")
    )
    pids = [(hit["pid"], hit.meta.id) for hit in query.scan()]
    errors = 0
    ids = []
    for idx, (pid, id) in enumerate(pids, 1):
        if patron := Patron.get_record_by_pid(pid):
            ids.append(id)
            try:
                patron["patron"]["communication_channel"] = CommunicationChannel.MAIL
                db.session.query(patron.model_cls).filter_by(id=patron.id).update(
                    {patron.model_cls.json: patron}
                )
            except Exception as err:
                LOGGER.error(f"{idx} * Update patron: {pid} {err}")
                errors += 1
    if ids:
        # commit session
        db.session.commit()
        # bulk indexing of patron records.
        indexer = PatronsIndexer()
        indexer.bulk_index(ids)
        indexer.process_bulk_queue()

    LOGGER.info(f"upgraded to version: {revision} errors: {errors}")


def downgrade():
    """Downgrade database."""
    # Nothing to do :: We can't set a false communication channel for patrons.
