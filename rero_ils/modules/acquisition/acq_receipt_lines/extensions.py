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

"""Acquisition Receipt line record extensions."""
from datetime import datetime

from flask_babel import gettext as _
from invenio_records.extensions import RecordExtension
from jsonschema import ValidationError
from sqlalchemy.orm.exc import NoResultFound


class AcquisitionReceiptLineCompleteDataExtension(RecordExtension):
    """Complete data about an acquisition receipt line."""

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized.

        If no receipt_date is given, use today's date as receipt_date.

        :param data: The dict passed to the record's constructor
        :param model: The model class used for initialization.
        """
        if not record.get('receipt_date'):
            record['receipt_date'] = datetime.now().strftime('%Y-%m-%d')


class AcqReceiptLineValidationExtension(RecordExtension):
    """Extension to validate data about acquisition receipt line."""

    @staticmethod
    def _check_received_quantity(record):
        """Calculate the received quantity.

        The total received quantity should not exceed the order_line.quantity.
        """
        if not record.quantity:
            return

        original_quantity = 0
        try:
            original_record = record.__class__.get_record(record.id)
            original_quantity = original_record.quantity
        except NoResultFound:
            # it's probably because the record isn't yet into DB (but `id`
            # field is already populated for very next integration)
            # As the record isn't yet into DB, the original_quantity keep 0
            pass

        quantity_to_check = record.quantity - original_quantity
        already_received_quantity = record.order_line.received_quantity
        new_total_quantity = quantity_to_check + already_received_quantity
        if new_total_quantity > record.order_line.quantity:
            msg = _('Received quantity is grower than ordered quantity')
            raise ValidationError(msg)

    # INVENIO EXTENSION HOOKS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def pre_commit(self, record):
        """Called before a record is committed."""
        AcqReceiptLineValidationExtension._check_received_quantity(record)

    pre_create = pre_commit
