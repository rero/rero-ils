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

"""Statistics resource database models."""


from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class StatIdentifier(RecordIdentifier):
    """Sequence generator for Stat identifiers."""

    __tablename__ = 'stat_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class StatMetadata(db.Model, RecordMetadataBase):
    """Stat record metadata."""

    __tablename__ = 'stat_metadata'


class StatType:
    """Type of statistics record."""

    BILLING = 'billing'
    LIBRARIAN = 'librarian'
    REPORT = 'report'


class StatIndicators:
    """Indicators of statistics reports."""

    NUMBER_OF_DOCUMENTS = 'number_of_documents'
    NUMBER_OF_SERIAL_HOLDINGS = 'number_of_serial_holdings'
    NUMBER_OF_ITEMS = 'number_of_items'
    NUMBER_OF_PATRONS = 'number_of_patrons'
    NUMBER_OF_ACTIVE_PATRONS = 'number_of_active_patrons'
    NUMBER_OF_ILL_REQUESTS = 'number_of_ill_requests'
    NUMBER_OF_DELETED_ITEMS = 'number_of_deleted_items'
    NUMBER_OF_CHECKINS = 'number_of_checkins'
    NUMBER_OF_CHECKOUTS = 'number_of_checkouts'
    NUMBER_OF_RENEWALS = 'number_of_renewals'
    NUMBER_OF_REQUESTS = 'number_of_requests'


class StatDistributions:
    """Distributions of statistics reports."""

    DOCUMENT_TYPE = 'document_type'
    GENDER = 'gender'
    IMPORTED = 'imported'
    ITEM_LOCATION = 'item_location'
    ITEM_OWNING_LIBRARY = 'item_owning_library'
    LIBRARY = 'library'
    LOCATION = 'location'
    PATRON_POSTAL_CODE = 'patron_postal_code'
    PATRON_TYPE = 'patron_type'
    ROLE = 'role'
    STATUS = 'status'
    TIME_RANGE_MONTH = 'time_range_month'
    TIME_RANGE_YEAR = 'time_range_year'
    TYPE = 'type'
    TRANSACTION_CHANNEL = 'transaction_channel'
