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

"""ApiHarvester tasks."""

from __future__ import absolute_import, print_function

import click
from celery import shared_task
from flask import current_app
from invenio_records_rest.utils import obj_or_import_string

from rero_ils.modules.utils import set_timestamp

from .utils import get_apiharvest_object


@shared_task(ignore_result=True, soft_time_limit=3600)
def harvest_records(name, from_date=None, harvest_count=-1, verbose=False):
    """Harvest records.

    :param name: name of API config tu harvest
    :param from_date: start date for harvesting
    :param harvest_count: how many records to harvest (-1 harvest all)
    :returns: count of harvested record and total of exsisting records
    """
    count = -1

    if config := get_apiharvest_object(name=name):
        if not from_date:
            from_date = config.lastrun.isoformat()
            if harvest_count < 0:
                config.update_lastrun()
        msg = f"API harvest {name} class name: {config.classname} "
        msg += f"from date: {from_date} url: {config.url}"

        current_app.logger.info(msg)
        HarvestClass = obj_or_import_string(config.classname)
        harvest = HarvestClass(
            name=name, verbose=verbose, harvest_count=harvest_count, process=True
        )
        count, total = harvest.harvest_records(from_date=from_date)
        msg = (
            f"API harvest {name} items={total} |"
            f" got={count} new={harvest.count_new}"
            f" updated={harvest.count_upd} deleted={harvest.count_del}"
        )
        if verbose:
            click.echo(msg)
        current_app.logger.info(msg)
        timestamp_data = {
            name: {
                "name": name,
                "totoal": total,
                "count": count,
                "new": harvest.count_new,
                "update": harvest.count_upd,
                "delete": harvest.count_del,
                "from": from_date,
                "max": harvest_count,
            }
        }
        set_timestamp("api_harvester", **timestamp_data)
    else:
        current_app.logger.error(f"No config found: {name}")
    return count, total
