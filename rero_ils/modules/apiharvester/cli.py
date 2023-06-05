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

"""Click command-line interface for mef contribution management."""

from __future__ import absolute_import, print_function

import click
import yaml
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from rero_ils.modules.apiharvester.tasks import harvest_records

from .models import ApiHarvestConfig
from .utils import api_source

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.group()
def apiharvester():
    """Api harvester commands."""


@apiharvester.command('source')
@click.argument('name')
@click.option('-U', '--url', default='', help='Url')
@click.option('-m', '--mimetype', default='', help='Mimetype')
@click.option('-s', '--size', default=-1, type=int, help='Size')
@click.option('-c', '--comment', default='', help='Comment')
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def api_source_config(name, url, mimetype, size, comment, update):
    """Add or Update ApiHarvestConfig."""
    click.echo(f'ApiHarvesterConfig: {name} ', nl=False)
    msg = api_source(
        name=name,
        url=url,
        mimetype=mimetype,
        size=size,
        comment=comment,
        update=update
    )
    click.echo(msg)


@apiharvester.command('sources')
@click.argument('configfile', type=click.File('rb'))
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def api_source_config_from_file(configfile, update):
    """Add or update ApiHarvestConfigs from file."""
    configs = yaml.load(configfile, Loader=yaml.FullLoader)
    for name, values in sorted(configs.items()):
        url = values.get('url', '')
        mimetype = values.get('mimetype', '')
        size = values.get('size', 100)
        comment = values.get('comment', '')
        click.echo(f'ApiHarvesterConfig: {name} {url} ', nl=False)
        msg = api_source(
            name=name,
            url=url,
            mimetype=mimetype,
            size=size,
            comment=comment,
            update=update
        )
        click.echo(msg)


@apiharvester.command('harvest')
@click.option('-n', '--name', default=None,
              help='Name of persistent configuration to use.')
@click.option('-f', '--from-date', default=None,
              help='The lower bound date for the harvesting (optional).')
@click.option('-u', '--url', default=None,
              help='The upper bound date for the harvesting (optional).')
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help='Enqueue harvesting and return immediately.')
@click.option('--signals/--no-signals', default=True,
              help='Signals sent with Api harvesting results.')
@click.option('-s', '--size', type=int, default=0,
              help='Size of chunks (optional).')
@click.option('-m', '--max_results', type=int, default=0,
              help='maximum of records to harvest (optional).')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def harvest(name, from_date, url, enqueue, signals, size, max_results,
            verbose):
    """Harvest api."""
    if name:
        click.secho(f'Harvest api: {name}', fg='green')
    elif url:
        click.secho(f'Harvest api: {url}', fg='green')
    if enqueue:
        harvest_records.delay(url=url, name=name, from_date=from_date,
                              signals=signals, size=size,
                              max_results=max_results, verbose=verbose)
    else:
        harvest_records(url=url, name=name, from_date=from_date,
                        signals=signals, size=size, max_results=max_results,
                        verbose=verbose)


@apiharvester.command('info')
@with_appcontext
def info():
    """List infos for tasks."""
    apis = ApiHarvestConfig.query.all()
    for api in apis:
        click.echo(api.name)
        click.echo(f'\tlastrun  : {api.lastrun}')
        click.echo(f'\turl      : {api.url}')
        click.echo(f'\tmimetype : {api.mimetype}')
        click.echo(f'\tsize     : {api.size}')
        click.echo(f'\tcomment  : {api.comment}')
