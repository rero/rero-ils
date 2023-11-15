# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Extension for AcqAccount records."""
from flask_babel import gettext as _
from invenio_records.extensions import RecordExtension
from jsonschema import ValidationError


class ParentAccountDistributionCheck(RecordExtension):
    """Extension to check if the parent account has enough money."""

    def _check_balance(self, record):
        """Check if parent balance has enough money."""
        original_record = record.__class__.get_record_by_pid(record.pid)
        amount_to_check = record.get('allocated_amount')
        if original_record:
            amount_to_check -= original_record.get('allocated_amount')
        parent = record.parent

        # If we grow the allocated amount:
        #  - Either record is a root account. In this case, nothing to check!
        #  - Either record has parent, we need to check if parent has enough
        #    balance to do that.
        if amount_to_check > 0 and parent:
            if parent.remaining_balance[0] < amount_to_check:
                msg = _('Parent account available amount too low')
                raise ValidationError(msg)

        # If we decrease the allocated amount:
        #  - Either record doesn't have any children : nothing to check!
        #  - Either record has child : we need to decrease more the record
        #    self balance (money still available for this account)
        if amount_to_check < 0 and record.get_children(output='count'):
            if original_record.remaining_balance[0] < abs(amount_to_check):
                msg = _('Remaining balance too low')
                raise ValidationError(msg)

    pre_commit = _check_balance
    pre_create = _check_balance
