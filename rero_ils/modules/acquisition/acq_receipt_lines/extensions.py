# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition Receipt line record extensions."""

import contextlib
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
        if not record.get("receipt_date"):
            record["receipt_date"] = datetime.now().strftime("%Y-%m-%d")


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
        with contextlib.suppress(NoResultFound):
            original_record = record.__class__.get_record(record.id)
            original_quantity = original_record.quantity
        quantity_to_check = record.quantity - original_quantity
        already_received_quantity = record.order_line.received_quantity
        new_total_quantity = quantity_to_check + already_received_quantity
        if new_total_quantity > record.order_line.quantity:
            msg = _("Received quantity is grower than ordered quantity")
            raise ValidationError(msg)

    # INVENIO EXTENSION HOOKS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def pre_commit(self, record):
        """Called before a record is committed."""
        AcqReceiptLineValidationExtension._check_received_quantity(record)

    pre_create = pre_commit
