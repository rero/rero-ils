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


class VendorIdentifier(RecordIdentifier):
    """Sequence generator for Vendor identifiers."""

    __tablename__ = 'vendor_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class VendorMetadata(db.Model, RecordMetadataBase):
    """Vendor record metadata."""

    __tablename__ = 'vendor_metadata'


class VendorContactType:
    """Type of vendor contact."""

    DEFAULT = 'default'
    ORDER = 'order'
    SERIAL = 'serial'


class VendorNoteType:
    """Type of vendor note."""

    ORDER = 'order_note'
    CLAIM = 'claim_note'
    RETURN = 'return_note'
    INVOICE = 'invoice_note'
    PAYMENT = 'payment_note'
    RECEIPT = 'receipt_note'
    CREDIT = 'credit_note'
    STAFF = 'staff_note'
    GENERAL = 'general_note'
