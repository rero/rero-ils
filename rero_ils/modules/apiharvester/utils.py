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

"""ApiHarvester utils."""

from __future__ import absolute_import, print_function

import click
import requests
from dateutil import parser
from flask import current_app
from invenio_db import db

from .models import ApiHarvestConfig
from .signals import apiharvest_part


def api_source(name, url='', mimetype='', size=100, comment='', update=False):
    """Add ApiHarvesterConfig."""
    with current_app.app_context():
        source = ApiHarvestConfig.query.filter_by(name=name).first()
        if not source:
            source = ApiHarvestConfig(
                name=name,
                url=url,
                mimetype=mimetype,
                size=100,
                comment=comment
            )
            source.save()
            db.session.commit()
            return 'Added'
        elif update:
            source.name = name
            msg = []
            if url != '':
                source.url = url
                msg.append(f'url:{url}')
            if mimetype != '':
                source.mimetype = mimetype
                msg.append(f'mimetype:{mimetype}')
            if size != -1:
                source.size = size
                msg.append(f'size:{size}')
            if comment != '':
                source.comment = comment
                msg.append(f'comment:{comment}')
            db.session.commit()
            return f'Updated: {", ".join(msg)}'
        return 'Not Updated'


def extract_records(data):
    """Extract a record from REST data."""
    records = []
    hits = data.get('hits', {}).get('hits', {})
    for hit in hits:
        # pid = data.get('id', '')
        # updated = data.get('updated', '')
        # links = data.get('links', {}).get('self', '')
        record = hit.get('metadata', '')
        records.append(record)
    return records


def get_records(url=None, name=None, from_date=None, max_results=0, size=100,
                signals=True, verbose=False, **kwargs):
    """Harvest multiple records from invenio api."""
    url += f'/?size={size}'
    if from_date:
        if isinstance(from_date, str):
            from_date = parser.parse(from_date)
        from_date = from_date.isoformat()
        # we have to urlencode the : from the time with \:
        from_date = from_date.replace(':', '%5C:')
        url += f'&q=_updated:>{from_date}'
    url += f'&size={size}'

    if verbose:
        click.echo(f'Get records from {url}')

    try:
        count = 0
        request = requests.get(url)
        data = request.json()

        total = data['hits']['total']['value']
        click.echo(f'API records found: {total}')

        next_url = data.get('links', {}).get('self', True)
        while next_url and (count < max_results or max_results == 0):
            records = extract_records(data)
            count += len(records)

            if count - max_results > 0 and max_results != 0:
                records = records[:max_results]

            request = requests.get(next_url)
            data = request.json()
            if signals:
                apiharvest_part.send(
                    records=records,
                    name=name,
                    url=next,
                    verbose=verbose,
                    **kwargs)
            else:
                yield next_url, records
            next_url = data.get('links', {}).get('next', None)
    except Exception as error:
        click.secho(
            f'Harvesting API ConnectionRefusedError: {error}',
            fg='red'
        )
        yield url, []
