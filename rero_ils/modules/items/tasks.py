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

"""Celery tasks for item records."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app

from .api import Item
from ..utils import extracted_data_from_ref, set_timestamp


@shared_task
def process_late_claimed_issues(
    expected_issues_to_late=True, create_first_claim=True,
        create_next_claim=True, dbcommit=True, reindex=True):
    """Job to manage serials claims.

    Receives the next late expected issue for all holdings.
    Creates the first and next claims for a late or claimed issues

    :param expected_issues_to_late: by default creates late issues.
    :param create_first_claim: by default creates first claims.
    :param create_next_claim: by default creates next claims.
    :param reindex: reindex the records.
    :param dbcommit: commit record to database.

    :return a count of modified and created issues.
    """
    expected_issues_to_late_count = 0
    create_first_claim_count = 0
    create_next_claim_count = 0

    if expected_issues_to_late:
        expected_issues_to_late_count = Item.receive_next_late_expected_issues(
            dbcommit=dbcommit, reindex=reindex)
    if create_first_claim:
        create_first_claim_count = Item.create_first_and_next_claims(
            claim_type='first', dbcommit=dbcommit, reindex=reindex)
    if create_next_claim:
        create_next_claim_count = Item.create_first_and_next_claims(
            claim_type='next', dbcommit=dbcommit, reindex=reindex)

    msg = 'expected_issues_to_late: {expected_issues_to_late_count} '\
        'create_first_claim: {create_first_claim_count} '\
        'create_next_claim: {create_next_claim_count} '.format(
            expected_issues_to_late_count=expected_issues_to_late_count,
            create_first_claim_count=create_first_claim_count,
            create_next_claim_count=create_next_claim_count
        )
    set_timestamp('claims-creation', msg=msg)
    return msg


@shared_task
def clean_obsolete_temporary_item_types():
    """Clean obsoletes temporary item_type for items.

    Search for all item with obsolete temporary item_type. For each found item,
    clean the temporary item_type informations. Update item into database to
    commit change
    """
    current_app.logger.debug("Starting clean_obsolete_temporary_item_types()"
                             " tasks ...")
    for item in Item.get_items_with_obsolete_temporary_item_type():
        # logger information
        tmp_itty_data = item['temporary_item_type']
        tmp_itty = extracted_data_from_ref(tmp_itty_data['$ref'], 'record')
        tmp_itty_enddate = tmp_itty_data['end_date']
        default_itty = extracted_data_from_ref(item['item_type']['$ref'],
                                               'record')
        msg = 'Removing temporary itty on item#{item_pid} :: [{tmp_itty}](' \
            '{tmp_date}) --> [{default_itty}]'.format(
                item_pid=item.pid,
                tmp_itty=tmp_itty.get('name'),
                tmp_date=tmp_itty_enddate,
                default_itty=default_itty.get('name')
            )
        current_app.logger.info(msg)
        # remove the obsolete data
        del item['temporary_item_type']
        item.replace(data=item, dbcommit=True, reindex=True)
    set_timestamp('clean_obsolete_temporary_item_types', msg=msg)
    current_app.logger.debug("Ending clean_obsolete_temporary_item_types()")
