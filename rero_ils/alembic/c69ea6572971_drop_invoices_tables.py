# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""Remove invoices and update the api harvester tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c69ea6572971"
down_revision = "8d97be2c8ad6"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.drop_table("acq_invoice_id")
    op.drop_table("acq_invoice_metadata")
    op.add_column(
        "apiharvester_config",
        sa.Column("classname", sa.String(length=255), nullable=False),
    )
    op.add_column("apiharvester_config", sa.Column("code", sa.Text(), nullable=True))
    op.drop_column("apiharvester_config", "comment")
    op.drop_column("apiharvester_config", "mimetype")
    op.drop_column("apiharvester_config", "size")
    op.drop_index("ix_uq_partial_files_object_is_head", table_name="files_object")
    # ### end Alembic commands ###


def downgrade():
    """Downgrade database."""
    op.create_index(
        "ix_uq_partial_files_object_is_head",
        "files_object",
        ["bucket_id", "key"],
        unique=False,
    )
    op.add_column(
        "apiharvester_config",
        sa.Column("size", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.add_column(
        "apiharvester_config",
        sa.Column(
            "mimetype", sa.VARCHAR(length=255), autoincrement=False, nullable=False
        ),
    )
    op.add_column(
        "apiharvester_config",
        sa.Column("comment", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.drop_column("apiharvester_config", "code")
    op.drop_column("apiharvester_config", "classname")
    op.create_table(
        "acq_invoice_metadata",
        sa.Column(
            "created", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "json",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("version_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_acq_invoice_metadata"),
    )
    op.create_table(
        "acq_invoice_id",
        sa.Column("recid", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("recid", name="pk_acq_invoice_id"),
    )
    # ### end Alembic commands ###
