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

"""Move collection to his own table."""

from logging import getLogger

from alembic import op
from invenio_db import db
from invenio_records.models import RecordMetadata

from rero_ils.modules.collections.models import CollectionMetadata

# revision identifiers, used by Alembic.
revision = "9e3145d88e64"
down_revision = "f0e7f3b80a21"
branch_labels = ()
depends_on = None

LOGGER = getLogger("alembic")
SCHEMA = "https://bib.rero.ch/schemas/collections/collection-v0.0.1.json"


def upgrade():
    """Upgrade database."""
    CollectionMetadata.metadata.create_all(bind=db.engine)
    assert CollectionMetadata.query.count() == 0
    results = RecordMetadata.query.filter(
        RecordMetadata.json["$schema"].as_string() == SCHEMA
    ).all()
    collections = [
        {
            "id": col.id,
            "json": col.json,
            "created": col.created,
            "updated": col.updated,
            "version_id": col.version_id,
        }
        for col in results
    ]
    op.bulk_insert(CollectionMetadata.__table__, collections)
    for col in results:
        db.session.delete(col)
    db.session.commit()
    LOGGER.info("migrate %s" % len(collections))


def downgrade():
    """Downgrade database."""
    assert (
        RecordMetadata.query.filter(
            RecordMetadata.json["$schema"].as_string() == SCHEMA
        ).count()
        == 0
    )
    results = CollectionMetadata.query.all()
    collections = [
        {
            "id": col.id,
            "json": col.json,
            "created": col.created,
            "updated": col.updated,
            "version_id": col.version_id,
        }
        for col in results
    ]
    op.bulk_insert(RecordMetadata.__table__, collections)
    # need to close the session before removing the table
    db.session.close()
    op.drop_table("collection_metadata")
    LOGGER.info("migrate %s record collection" % len(collections))
