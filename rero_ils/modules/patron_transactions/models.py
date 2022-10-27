# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Define relation between records and buckets."""

from __future__ import absolute_import

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class PatronTransactionIdentifier(RecordIdentifier):
    """Sequence generator for Patron Transaction identifiers."""

    __tablename__ = 'patron_transaction_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class PatronTransactionMetadata(db.Model, RecordMetadataBase):
    """PatronTransaction record metadata."""

    __tablename__ = 'patron_transaction_metadata'


class PatronTransactionStatus:
    """PatronTransaction status."""

    OPEN = 'open'
    CLOSED = 'closed'


class PatronTransactionType:
    """PatronTransaction type."""

    DAMAGED = 'damaged'
    ILL = 'interlibrary_loan'
    LOST = 'lost'
    OTHER = 'other'
    OVERDUE = 'overdue'
    PHOTOCOPY = 'photocopy'
    SUBSCRIPTION = 'subscription'
