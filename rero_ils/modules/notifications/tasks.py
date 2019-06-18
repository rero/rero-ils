# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2019 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Celery tasks for notification records."""

from __future__ import absolute_import, print_function

from celery import shared_task

from ..loans.api import get_due_soon_loans, get_overdue_loans


@shared_task(ignore_result=True)
def create_over_and_due_soon_notifications():
    """Creates due_soon and overdue notifications."""
    over_due_loans = get_overdue_loans()
    no_over_due_loans = 0
    for loan in over_due_loans:
        loan.create_notification(notification_type='overdue')
        no_over_due_loans += 1

    due_soon_loans = get_due_soon_loans()
    no_due_soon_loans = 0
    for loan in due_soon_loans:
        loan.create_notification(notification_type='due_soon')
        no_due_soon_loans += 1

    return 'created {no_over_due_loans} overdue loans, '\
        '{no_due_soon_loans} due soon loans'.format(
            no_over_due_loans=no_over_due_loans,
            no_due_soon_loans=no_due_soon_loans)
