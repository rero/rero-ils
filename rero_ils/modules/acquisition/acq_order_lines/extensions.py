# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Extension for acquisition account records."""

from flask_babel import gettext as _
from invenio_records.extensions import RecordExtension
from jsonschema import ValidationError

from rero_ils.modules.acquisition.acq_accounts.models import \
    AcqAccountExceedanceType


class AcqOrderLineValidationExtension(RecordExtension):
    """Extension to validate data about acquisition order line."""

    @staticmethod
    def _check_balance(record):
        """Check if parent account balance has enough money."""
        # compute the total amount of the order line
        record['total_amount'] = record['amount'] * record['quantity'] \
            - record.get('discount_amount', 0)

        original_record = record.__class__.get_record_by_pid(record.pid)

        # compute the amount to check ; 2 possibilities :
        #   - either the account doesn't change : in such case, we need to
        #     check the possible difference between original record and updated
        #     record total_amount.
        #   - either the account changes : in such case, we need to the check
        #     if the new destination account balance accept this order line.
        amount_to_check = record.get('total_amount', 0)
        if original_record and original_record.account == record.account:
            amount_to_check -= original_record.get('total_amount', 0)

        # If we decease the total amount of this order line, no need to check.
        # There will just be more available money on the related account. Enjoy
        # the life.
        #
        # If the total amount increase, then check if the related account has
        # enough money to validate this change. If not, then raise a
        # ValidationError.
        if amount_to_check > 0:
            account = record.account
            available_money = account.remaining_balance[0] \
                + account.get_exceedance(AcqAccountExceedanceType.ENCUMBRANCE)
            if available_money < amount_to_check:
                msg = _('Parent account available amount too low')
                raise ValidationError(msg)

    @staticmethod
    def _check_harvested(record):
        """Harvested document cannot be linked to an order line."""
        related_document = record.document
        if related_document and related_document.harvested:
            msg = _('Cannot link to an harvested document')
            raise ValidationError(msg)

    # INVENIO EXTENSION HOOKS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def pre_commit(self, record):
        """Called before a record is committed."""
        AcqOrderLineValidationExtension._check_balance(record)
        AcqOrderLineValidationExtension._check_harvested(record)

    pre_create = pre_commit
