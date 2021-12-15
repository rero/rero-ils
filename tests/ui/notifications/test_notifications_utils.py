# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Notification utils tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from random import randint

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.utils import get_circ_policy
from rero_ils.modules.notifications.utils import calculate_notification_amount


def test_notification_calculate_notification_amount(
   notification_due_soon_martigny
):
    """Test calculate amount for a notifications."""
    notification = notification_due_soon_martigny
    loan = Loan.get_record_by_pid(notification.loan_pid)
    cipo = get_circ_policy(loan)

    original_cipo = deepcopy(cipo)
    original_notification = deepcopy(notification)

    # STEP 0 :: As specified into the fixture, there is no fee for a
    #           'due_soon' reminder.
    assert calculate_notification_amount(notification) == 0

    # STEP 1 :: Update the related cipo specify an amount for the first
    #           'due_soon' reminder. Check the notification amount according
    #           to this new setting
    fee_amount = randint(1, 100)
    reminder = cipo.get_reminder(DUE_SOON_REMINDER_TYPE)
    reminder['fee_amount'] = fee_amount
    cipo['reminders'] = [reminder]
    cipo.update(cipo, dbcommit=True, reindex=True)
    assert calculate_notification_amount(notification) == fee_amount

    # STEP 2 :: Update the notification context to simulate it's the second
    #           'due_soon' reminders notification. Check the notification
    #           amount accord to this new setting
    counter = notification['context']['reminder_counter']
    notification['context']['reminder_counter'] = counter + 1
    assert calculate_notification_amount(notification) == 0

    # STEP 3 :: Delete the cipo reminders setting. As there is no setting, the
    #           caclulted amount must be equals to 0
    del cipo['reminders']
    cipo.update(cipo, dbcommit=True, reindex=True)
    assert calculate_notification_amount(notification) == 0

    # Reset fixtures
    cipo.update(original_cipo, dbcommit=True, reindex=True)
    notification.update(original_notification, dbcommit=True, reindex=True)
