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

"""Signals connector for patron."""

from datetime import datetime

from .api import Patron, PatronsSearch
from ..patron_types.api import PatronType
from ..utils import add_years, get_schema_for_resource


def enrich_patron_data(sender, json=None, record=None, index=None,
                       doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == PatronsSearch.Meta.index:
        patron = record
        if not isinstance(record, Patron):
            patron = Patron.get_record_by_pid(record.get('pid'))
        org_pid = patron.get_organisation()['pid']
        if org_pid:
            json['organisation'] = {
                'pid': org_pid
            }

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
    if record.get('$schema') != get_schema_for_resource(Patron):
        return
    if record.patron_type_pid is None:
        return
    ptty = PatronType.get_record_by_pid(record.patron_type_pid)
    if ptty.is_subscription_required and not record.has_valid_subscription:
        # TODO : (2020-03-27)
        #   At this time, subscription are only possible for one year. In
        #   the future, the subscription period should be defined as a
        #   patron_type attribute.
        start_date = datetime.now()
        end_date = add_years(start_date, 1)
        record.add_subscription(ptty, start_date, end_date)


def update_from_profile(sender, profile=None, **kwargs):
    """Update the patron linked with the user profile data.

    :param profile - the rero user profile
    """
    patron = Patron.get_patron_by_user(profile.user)
    if patron:
        old_keep_history = patron.get('patron', {}).get('keep_history')
        patron.reindex()
        from ..loans.api import anonymize_loans
        new_keep_history = profile.keep_history
        if old_keep_history and not new_keep_history:
            anonymize_loans(
                patron_data=patron,
                patron_pid=patron.get('pid'),
                dbcommit=True,
                reindex=True)
