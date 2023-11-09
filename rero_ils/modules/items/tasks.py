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

"""Celery tasks for item records."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.holdings.utils import create_next_late_expected_issues
from rero_ils.modules.utils import extracted_data_from_ref, set_timestamp

from .api import Item
from .utils import get_provisional_items_candidate_to_delete, \
    update_late_expected_issue


@shared_task()
def delete_provisional_items():
    """Delete checked-in provisional items.

    For the list of candidates item pids to delete, this method tries to delete
    each item. The item will not be deleted if the method `can_delete` is True.
    The reasons not to delete a provisional item are the same as other items:
      1) no active loans
      2) no fees
    """
    deleted_items, counter = 0, 0
    for item in get_provisional_items_candidate_to_delete():
        counter += 1
        try:
            item.delete(dbcommit=True, delindex=True)
            deleted_items += 1
        except IlsRecordError.NotDeleted:
            pass
        except Exception as error:
            current_app.logger.error(error)

    msg_dict = {
        'number_of_candidate_items_to_delete': counter,
        'number_of_deleted_items': deleted_items
    }
    set_timestamp('claims-creation', **msg_dict)
    return msg_dict


@shared_task
def process_late_issues(dbcommit=True, reindex=True):
    """Job to manage late issues.

    Receives the next late expected issue for all holdings.

    :param reindex: reindex the records.
    :param dbcommit: commit record to database.
    :return: number of modified or created issues.
    """
    # Perform serial type holding with passed `next_expected_date`
    counter = create_next_late_expected_issues(
        dbcommit=dbcommit, reindex=reindex)
    # Perform already created issue with passed `next_expected_date`
    counter += update_late_expected_issue(dbcommit=dbcommit, reindex=reindex)
    msg = f'expected_issues_to_late: {counter}'
    set_timestamp('late-issues-creation', msg=msg)
    return msg


@shared_task
def clean_obsolete_temporary_item_types_and_locations():
    """Clean obsoletes temporary item_type for items.

    Search for all item with obsolete temporary item_type. For each found item,
    clean the temporary item_type informations. Update item into database to
    commit change
    """
    counter = 0
    for item, field_type in \
            Item.get_items_with_obsolete_temporary_item_type_or_location():
        counter += 1
        if field_type == 'itty':
            tmp_itty_data = item.pop('temporary_item_type', {})
            tmp_itty_name = extracted_data_from_ref(
                tmp_itty_data['$ref'], 'record').get('name')
            tmp_itty_enddate = tmp_itty_data['end_date']
            msg = f'Removed obsolete temporary_item_type {tmp_itty_name} \
                    {tmp_itty_enddate} from item pid {item.pid}'
        elif field_type == 'loc':
            tmp_loc_data = item.pop('temporary_location', {})
            tmp_loc_name = extracted_data_from_ref(
                tmp_loc_data['$ref'], 'record').get('name')
            tmp_loc_enddate = tmp_loc_data['end_date']
            msg = f'Removed obsolete temporary_location {tmp_loc_name} \
                    {tmp_loc_enddate} from item pid {item.pid}'
        current_app.logger.info(msg)
        item.update(item, dbcommit=True, reindex=True)
    count = {'deleted fields': counter}
    set_timestamp('clean_obsolete_temporary_item_types_and_locations', **count)
    return count


@shared_task
def delete_holding(holding_pid, force=False, dbcommit=True, delindex=True):
    """Delete holding."""
    if holding_pid:
        holding_rec = Holding.get_record_by_pid(holding_pid)
        try:
            # TODO: Need to split DB and elasticsearch deletion.
            holding_rec.delete(force=force, dbcommit=dbcommit,
                               delindex=delindex)
        except IlsRecordError.NotDeleted:
            current_app.logger.warning(f'Holding not deleted: {holding_pid}')
