# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
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

"""ApiHarvester tasks."""

from __future__ import absolute_import, print_function

from celery import shared_task

from .models import ApiHarvestConfig
from .utils import get_records


@shared_task(ignore_result=True)
def harvest_records(url=None, name=None, from_date=None, size=0,
                    verbose=False):
    """Harvest records."""
    config = ApiHarvestConfig.query.filter_by(name=name).first()
    if config:
        if not url:
            url = config.url
        if not from_date:
            from_date = config.lastrun
            config.update_lastrun()
        if size == 0:
            size = config.size

    # TODO signal or yield
    for next, records in get_records(
        url=url, name=name, from_date=from_date, size=size,
        signals=True, verbose=verbose
    ):
        # TODO signal was false and we have to process records here
        pass
