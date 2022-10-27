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

"""Signals connections for ebooks document."""

import click
from flask import current_app

from .tasks import create_mef_records


def publish_api_harvested_records(sender=None, records=None, name='', url=None,
                                  verbose=False, *args, **kwargs):
    """Create, index the harvested records."""
    assert url
    if name == 'mef':
        converted_records = []
        js = current_app.extensions.get('invenio-jsonschemas')
        path = current_app.config.get('RERO_ILS_CONTRIBUTIONS_MEF_SCHEMA')
        url = js.path_to_url(path)
        if records:
            for record in records:
                record['$schema'] = url
                converted_records.append(record)
            click.echo(
                f'mef harvester: received {len(records)} records: {url}'
            )
            create_mef_records(converted_records, verbose)
        else:
            current_app.logger.info('publish_harvester: nothing to do')
