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
    es_query = HoldingsSearch() \
        .filter('term', holdings_type='standard') \
        .filter('term', items_count=0) \
        .source('pid')
    errors = 0
    for hit in [hit for hit in es_query.scan()]:
        record = Holding.get_record(hit.meta.id)
        try:
            record.delete(force=False, dbcommit=True, delindex=True)
        except Exception as err:
            errors += 1
            reasons = record.reasons_not_to_delete()
            current_app.logger.error(
                f'Can not delete standard holding: {hit.pid} {reasons} {err}')

    counts = {'count': es_query.count(), 'errors': errors}
    set_timestamp('delete_standard_holdings_having_no_items', **counts)
    return counts
