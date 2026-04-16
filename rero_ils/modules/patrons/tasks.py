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

from datetime import UTC, datetime

from celery import shared_task
from flask import current_app

from rero_ils.modules.loans.api import LoansSearch
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.users.api import User
from rero_ils.modules.users.models import UserRole

from ..patron_types.api import PatronType
from ..utils import add_years, set_timestamp
from .api import Patron, PatronsSearch


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
        sub_end_date = subscription.get("end_date", "1970-01-01")
        sub_end_date = datetime.strptime(sub_end_date, "%Y-%m-%d")
        return sub_end_date < end_date

    for patron in Patron.patrons_with_obsolete_subscription_pids():
        subscriptions = patron.patron.get("subscriptions", [])
        subscriptions = [sub for sub in subscriptions if not is_obsolete(sub)]
        if not subscriptions and "subscriptions" in patron.patron:
            del patron["patron"]["subscriptions"]
        else:
            patron["patron"]["subscriptions"] = subscriptions

        # DEV NOTE : this update will trigger the listener
        #     `create_subscription_patron_transaction`. This listener will
        #     create a new subscription if needed
        patron.update(User.remove_fields(patron.dumps()), dbcommit=True, reindex=True)


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
            msg = f"Add a subscription for patron#{patron.pid} ... it shouldn't happen !!"
            current_app.logger.error(msg)
            start_date = datetime.now()
            end_date = add_years(start_date, 1)
            patron.add_subscription(ptty, start_date, end_date)


@shared_task(ignore_result=True)
def task_clear_and_renew_subscriptions():
    """Clean obsolete subscriptions and renew subscription if needed."""
    clean_obsolete_subscriptions()
    check_patron_types_and_add_subscriptions()
    set_timestamp("clear_and_renew_subscriptions")


def _delete_inactive_patrons_for_org(org_pid, config, dry_run=False):
    """Process one organisation's inactive patron cleanup.

    :param org_pid: the organisation pid.
    :param config: the patron_cleanup configuration dict.
    :param dry_run: if True, log candidates without deleting.
    :returns: tuple (deleted_count, skipped_count).
    """
    now = datetime.now(UTC)
    expiration_cutoff = add_years(now, -config["expiration_years"])
    inactivity_cutoff = add_years(now, -config["inactivity_years"])
    excluded_ptty_pids = set(config.get("excluded_patron_types", []))

    # ES pre-filter: patron role, expired, not blocked, not professional
    query = (
        PatronsSearch()
        .filter("term", organisation__pid=org_pid)
        .filter("term", roles=UserRole.PATRON)
        .filter("range", patron__expiration_date={"lt": expiration_cutoff.strftime("%Y-%m-%d")})
        .exclude("term", patron__blocked=True)
        .exclude("terms", roles=list(UserRole.PROFESSIONAL_ROLES))
        .source(["pid", "patron.type.pid", "user_id"])
    )

    deleted = 0
    skipped = 0
    for hit in query.scan():
        # Criterion: patron_type not in exclusion list
        if hit.patron.type.pid in excluded_ptty_pids:
            skipped += 1
            continue

        # Criterion: last connection date
        patron = Patron.get_record_by_pid(hit.pid)
        user = patron.user
        last_login = user.current_login_at or user.last_login_at
        if last_login and last_login > inactivity_cutoff:
            skipped += 1
            continue

        # Criterion: no active links (loans, open transactions, ILL requests, templates)
        if patron.get_links_to_me():
            skipped += 1
            continue

        # Criterion: no non-anonymized historical loans
        non_anon_count = (
            LoansSearch()
            .filter("term", to_anonymize=False)
            .filter("terms", state=[LoanState.CANCELLED, LoanState.ITEM_RETURNED])
            .filter("term", patron_pid=patron.pid)
            .count()
        )
        if non_anon_count:
            skipped += 1
            continue

        # All criteria met
        if dry_run:
            current_app.logger.info(f"[DRY RUN] Would delete patron {patron.pid} (org={org_pid})")
        else:
            patron.delete(force=False, dbcommit=True, delindex=True)
        deleted += 1

    current_app.logger.info(
        f"Patron cleanup for org {org_pid}: deleted={deleted}, skipped={skipped}{' (dry run)' if dry_run else ''}"
    )
    return deleted, skipped


@shared_task(ignore_result=True)
def task_delete_inactive_patrons(dry_run=False):
    """Delete inactive patron profiles for all organisations.

    :param dry_run: if True, log candidates without deleting them.
    """
    delete_inactive_patrons = {}
    for org in Organisation.get_all():
        if config := org.get("patron_cleanup"):
            deleted, skipped = _delete_inactive_patrons_for_org(org.pid, config, dry_run=dry_run)
            delete_inactive_patrons[org.pid] = {
                "deleted": deleted,
                "skipped": skipped,
            }
    if not dry_run:
        set_timestamp("delete_inactive_patrons", **delete_inactive_patrons)
