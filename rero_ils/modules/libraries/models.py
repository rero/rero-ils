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


class LibraryIdentifier(RecordIdentifier):
    """Sequence generator for Library identifiers."""

    __tablename__ = 'library_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class LibraryMetadata(db.Model, RecordMetadataBase):
    """Library record metadata."""

    __tablename__ = 'library_metadata'


class LibraryAddressType:
    """Address type for libraries."""

    MAIN_ADDRESS = 'main'
    SHIPPING_ADDRESS = 'shipping'
    BILLING_ADDRESS = 'billing'


class AccountTransferOption:
    """Allowed account transfer option for rollover setting."""

    NO_TRANSFER = 'rollover_no_transfer'
    ALLOCATED_AMOUNT = 'rollover_allocated_amount'
