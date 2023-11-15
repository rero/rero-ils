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

"""Celery tasks for patrons records."""

from __future__ import absolute_import, print_function

from datetime import datetime

from celery import shared_task
from flask import current_app

from rero_ils.modules.users.api import User

from .api import Patron
from ..patron_types.api import PatronType
from ..utils import add_years, set_timestamp


def clean_obsolete_subscriptions():
    """Clean obsoletes subscriptions from all patrons.

    Search for all patron with obsolete subscriptions. For each found patron
    clean the subscription array keeping only subscription with a end-time
    grower than now(). Update patron to commit change
    """
    def is_obsolete(subscription, end_date=None):
        """Check if a subscription is obsolete by checking end date."""
        if end_date is None:
            end_date = datetime.now()
        sub_end_date = subscription.get('end_date', '1970-01-01')
        sub_end_date = datetime.strptime(sub_end_date, '%Y-%m-%d')
        return sub_end_date < end_date

    for patron in Patron.patrons_with_obsolete_subscription_pids():
        subscriptions = patron.patron.get('subscriptions', [])
        subscriptions = [sub for sub in subscriptions if not is_obsolete(sub)]
        if not subscriptions and 'subscriptions' in patron.patron:
            del patron['patron']['subscriptions']
        else:
            patron['patron']['subscriptions'] = subscriptions

        # DEV NOTE : this update will trigger the listener
        #     `create_subscription_patron_transaction`. This listener will
        #     create a new subscription if needed
        patron.update(
            User.remove_fields(patron.dumps()),
            dbcommit=True,
            reindex=True
        )


def check_patron_types_and_add_subscriptions():
    """Check patron types with subscription amount and add subscriptions.

    Search for patron_type requiring a subscription. For each patron_type
    search about patron linked to it and without valid subscription. For
    each of these patrons, create a new subscription if needed.
    """
    # Note this function should never doing anything because never any patron
    # linked to these patron types shouldn't have no subscription. This is
    # because, a listener creating an active subscription is linked to signal
    # create/update for any patron. In addition, the method
    # `clean_obsolete_subscriptions`, at the last loop instruction will update
    # the patron ; this update will trigger the same listener and so create a
    # new active subscription is necessary.
    for ptty in PatronType.get_yearly_subscription_patron_types():
        patron_no_subsc = Patron.get_patrons_without_subscription(ptty.pid)
        for patron in patron_no_subsc:
            msg = f'Add a subscription for patron#{patron.pid} ... ' \
                  'it shouldn\'t happen !!'
            current_app.logger.error(msg)
            start_date = datetime.now()
            end_date = add_years(start_date, 1)
            patron.add_subscription(ptty, start_date, end_date)


@shared_task(ignore_result=True)
def task_clear_and_renew_subscriptions():
    """Clean obsolete subscriptions and renew subscription if needed."""
    clean_obsolete_subscriptions()
    check_patron_types_and_add_subscriptions()
    set_timestamp('clear_and_renew_subscriptions')
