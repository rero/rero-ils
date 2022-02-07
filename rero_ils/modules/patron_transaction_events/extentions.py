# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""PatronTransactionEvent record extensions."""

from invenio_records.extensions import RecordExtension
from jsonschema import ValidationError


class DecimalAmountExtension(RecordExtension):
    """Check and transform a decimal amount into integer representation."""

    def __init__(self, field_name, decimals=2):
        """Extension initialization.

        :param field_name: the field name where found the amount to analyze.
        :param decimals: the number of decimal accepted.
        """
        self.amount_field = field_name
        self.multiplier = pow(10, decimals)

    def _check_amount(self, record):
        """Check if the record has the correct decimal number.

        :param record: the record to validate.
        :raise ValidationError if the amount doesn't respect the decimal amount
        """
        # Check `self.amount_field` exists into the record. If not, we can
        # return without record modification.
        if self.amount_field not in record:
            return

        # Check that the amount field has the correct decimals. If not, a
        # `ValidationError` error will be raised.
        # NOTE:
        #   an amount of "123,450" is true despite if we configure only 2
        #   decimals. In same way "123,4" is also a valid value.
        # DEV NOTE :
        #   rounding the number, keeping one decimal will prevent the floating
        #   numbers problem
        #   >>> 2.2 * 100              --> 220.00000000000003
        #   >>> round(2.2 * 100, 1)    --> 220.0
        #   >>> round(2.234 * 100, 1)  --> 223.4
        #   >>> round(2.2345 * 100, 1) --> 223.5
        quotient = round(record[self.amount_field] * self.multiplier, 1)
        if (quotient % 1) != 0:
            decimal = 1 / self.multiplier
            msg = f'`{self.amount_field}` must be multiple of {decimal}'
            raise ValidationError(msg)

    pre_commit = _check_amount
    pre_create = _check_amount
