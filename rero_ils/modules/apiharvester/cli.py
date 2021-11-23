# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from .api import ApiHarvester
from .tasks import harvest_records

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def print_info(config, exists=False):
    """Print config info."""
    if exists:
        click.secho(f'{config.name} exists in DB', fg='yellow')
    else:
        click.echo(f'{config.name}')
    click.echo(f'  lastrun : {config.lastrun}')
    click.echo(f'  url     : {config.url}')
    click.echo(f'  size    : {config.size}')


@click.group()
def apiharvester():
    """Api harvester commands."""


@apiharvester.command()
@click.argument('name')
@click.option('-f', '--from-date', default=None,
              help='The lower bound date for the harvesting (optional).')
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help='Enqueue harvesting and return immediately.')
@click.option('-m', '--max', type=int, default=0,
              help='maximum of records to harvest (optional).')
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def harvest(name, from_date, enqueue, max, verbose):
    """API harvester run."""
    if name:
        click.secho(f'API harvester harvest: {name}', fg='green')
    if enqueue:
        process_id = harvest_records.delay(name=name, from_date=from_date,
                                           max=max, verbose=verbose)
        click.echo(f'Harvest started: {process_id}')
    else:
        count = harvest_records(name=name, from_date=from_date, max=max,
                                verbose=verbose)
        click.echo(f'Harvested: {count}')


@apiharvester.command()
@with_appcontext
def info():
    """API harvester configurations."""
    click.secho(f'API harvester configurations:', fg='green')
    for config in ApiHarvester.get_all_configs():
        print_info(config)


@apiharvester.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def init(verbose):
    """Api harvester configuration init."""
    click.secho(f'API harvester init', fg='green')
    configs = current_app.config.get('RERO_ILS_API_HARVESTER', {})
    for name, data in configs.items():
        db_config = ApiHarvester(name)
        exists = True
        if not db_config:
            exists = False
            db_config = ApiHarvester.create(name=name, url=data['url'],
                                            size=data['size'])
        if verbose:
            print_info(db_config, exists=exists)


@apiharvester.command()
@click.argument('name')
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def delete(name, verbose):
    """Api harvester configuration delete."""
    click.secho(f'API harvester delete: {name}', fg='red')
    db_config = ApiHarvester(name)
    if db_config:
        if verbose:
            print_info(db_config)
        db_config.delete()
    else:
        click.secho(f'Config not found!', fg='yellow')


@apiharvester.command()
@click.argument('name')
@click.option('-l', '--lastrun', default=None,
              type=click.DateTime(formats=['%Y-%m-%d', '%Y-%m-%d %H:%M:%S']))
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def set_lastrun(name, lastrun, verbose):
    """Api harvester set config."""
    click.secho(
        f'API harvester set lastrun: {name} {lastrun if lastrun else ""}',
        fg='green'
    )
    config = ApiHarvester(name)
    if config:
        config.update_lastrun(new_date=lastrun)
        if verbose:
            print_info(config)
    else:
        click.secho(f'Config not found!', fg='yellow')


@apiharvester.command()
@click.argument('name')
@click.option('-n', '--newname', default=None)
@click.option('-u', '--url', default=None)
@click.option('-s', '--size', type=int, default=None)
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def update(name, newname, url, size, verbose):
    """Api harvester set size."""
    click.secho(f'API harvester update: {name}', fg='green')
    config = ApiHarvester(name)
    if config:
        config.update(name=newname, url=url, size=size)
        if verbose:
            print_info(config)
    else:
        click.secho(f'Config not found!', fg='yellow')
