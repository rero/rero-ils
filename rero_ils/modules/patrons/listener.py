# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for patron."""

from datetime import datetime

from ..patron_types.api import PatronType
from ..utils import add_years
from .api import Patron, PatronsSearch


def enrich_patron_data(
    sender,
    json=None,
    record=None,
    index=None,
    doc_type=None,
    arguments=None,
    **dummy_kwargs,
):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split("-")[0] == PatronsSearch.Meta.index:
        patron = record
        if not isinstance(record, Patron):
            patron = Patron.get_record_by_pid(record.get("pid"))
        if org_pid := patron.organisation["pid"]:
            json["organisation"] = {"pid": org_pid}


def create_subscription_patron_transaction(sender, record=None, **kwargs):
    """This method check the patron to know if a subscription is requested.

    This method checks the patron_type linked to a patron and determine if
    a new subscription patron transaction should be created or not. If a
    subscriotion is needed, then the 'subscription' patron attribute will be
    updated.
    This method should be connect with 'before_record_insert' and
    'before_record_update'.

    :param record: the record being performed
    """
    if isinstance(record, Patron) and record.patron_type_pid:
        ptty = PatronType.get_record_by_pid(record.patron_type_pid)
        if ptty.is_subscription_required and not record.has_valid_subscription:
            # TODO : (2020-03-27)
            #   At this time, subscription are only possible for one year. In
            #   the future, the subscription period should be defined as a
            #   patron_type attribute.
            start_date = datetime.now()
            end_date = add_years(start_date, 1)
            record.add_subscription(ptty, start_date, end_date)


def update_from_profile(sender, user, **kwargs):
    """Update the patron linked with the user profile data.

    :param profile - the rero user profile
    """
    for patron in Patron.get_patrons_by_user(user):
        patron.reindex()
