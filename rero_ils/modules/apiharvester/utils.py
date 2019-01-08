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
                msg.append('url:{}'.format(url))
            if mimetype != '':
                source.mimetype = mimetype
                msg.append('mimetype:{}'.format(mimetype))
            if size != -1:
                source.size = size
                msg.append('size:{}'.format(size))
            if comment != '':
                source.comment = comment
                msg.append('comment:{}'.format(comment))
            db.session.commit()
            return 'Updated: {}'.format(', '.join(msg))
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


def get_records(url=None, name=None, from_date=None, max=0, size=100,
                signals=True, verbose=False, **kwargs):
    """Harvest multiple records from invenio api."""
    url += '/?size={0}'.format(size)
    if from_date:
        if isinstance(from_date, str):
            from_date = parser.parse(from_date)
        from_date = from_date.isoformat()
        # we have to urlencode the : from the time with \:
        from_date = from_date.replace(':', '%5C:')
        url += '&q=_updated:>{from_date}'.format(from_date=from_date)
    url += '&size={size}'.format(size=size)

    if verbose:
        click.echo('Get records from {url}'.format(url=url))

    try:
        count = 0
        request = requests.get(url)
        data = request.json()

        total = data.get('hits', {}).get('total', 0)
        click.echo(
            'API records found: {total}'.format(total=total)
        )

        next = data.get('links', {}).get('self', True)
        while next and (count < max or max == 0):
            records = extract_records(data)
            count += len(records)

            if count - max > 0 and max != 0:
                records = records[:max]

            request = requests.get(next)
            data = request.json()
            if signals:
                apiharvest_part.send(
                    records=records,
                    name=name,
                    url=next,
                    verbose=verbose,
                    **kwargs)
            else:
                yield next, records
            next = data.get('links', {}).get('next', None)
    except Exception as e:
        click.secho(
            'Harvesting API ConnectionRefusedError: {e}'.format(e=e),
            fg='red'
        )
        return 0, url, []
