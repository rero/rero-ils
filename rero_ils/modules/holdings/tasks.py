# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Celery tasks for holdings records."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app

from .api import Holding, HoldingsSearch
from ..utils import set_timestamp


@shared_task(ignore_result=True)
def delete_standard_holdings_having_no_items():
    """Removes standard holdings records with no attached items."""
    current_app.logger.debug(
        "Starting delete_standard_holdings_having_no_items task ...")
    es_query = HoldingsSearch() \
        .filter('term', holdings_type='standard') \
        .filter('term', items_count=0) \
        .source('pid')

    deleted = 0
    for hit in es_query.scan():
        record = Holding.get_record_by_pid(hit.pid)
        record.delete(force=False, dbcommit=True, delindex=True)
        deleted += 1

    current_app.logger.debug("Ending delete_standard_holdings_having_no_items")
    msg = f'Number of removed holdings: {es_query.count()}'
    set_timestamp('holdings-deletion', deleted=deleted)
    return msg
