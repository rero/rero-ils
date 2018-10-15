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

"""Signals connections for ebooks document."""

import click
from flask import current_app

from .tasks import create_mef_records


def publish_api_harvested_records(sender=None, records=[], *args, **kwargs):
    """Create, index the harvested records."""
    name = kwargs['name']
    url = kwargs['url']
    verbose = kwargs.get('verbose', False)
    if name == 'mef':
        converted_records = []
        js = current_app.extensions.get('invenio-jsonschemas')
        path = current_app.config.get('RERO_ILS_PERSONS_MEF_SCHEMA')
        url = js.path_to_url(path)
        for record in records:
            record['$schema'] = url
            converted_records.append(record)
        if records:
            click.echo(
                'mef harvester: received {count} records: {url}'.format(
                    count=len(records),
                    url=url
                )
            )

            create_mef_records(converted_records, verbose)
        else:
            current_app.logger.info('publish_harvester: nothing to do')
