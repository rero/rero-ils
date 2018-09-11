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

"""Click command-line interface for mef person management."""

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
@click.argument('url')
@click.option('-m', '--mimetype', default='', help='Mimetype')
@click.option('-s', '--size', default=100, help='Size')
@click.option('-c', '--comment', default='', help='Comment')
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def api_source_config(name, url, size, mimetype, comment, update):
    """Add or Update ApiHarvestConfig."""
    click.echo('ApiHarvesterConfig: {0} '.format(name), nl=False)
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
    configs = yaml.load(configfile)
    for name, values in sorted(configs.items()):
        url = values['url']
        mimetype = values.get('mimetype', '')
        size = values.get('size', 100)
        comment = values.get('comment', '')
        click.echo(
            'ApiHarvesterConfig: {0} {1} '.format(name, url), nl=False
        )
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
              help="Name of persistent configuration to use.")
@click.option('-f', '--from-date', default=None,
              help="The lower bound date for the harvesting (optional).")
@click.option('-u', '--url', default=None,
              help="The upper bound date for the harvesting (optional).")
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help="Enqueue harvesting and return immediately.")
@click.option('-s', '--size', default=100,
              help="Size of chunks (optional).")
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@with_appcontext
def harvest(name, from_date, url, enqueue, size, verbose):
    """Harvest api."""
    if name:
        click.secho('Harvest api: {0}'.format(name), fg='green')
    elif url:
        click.secho('Harvest api: {0}'.format(url), fg='green')
    size = current_app.config.get('RERO_ILS_MEF_RESULT_SIZE', 100)
    if enqueue:
        harvest_records.delay(url=url, name=name, from_date=from_date,
                              size=size,  verbose=verbose)
    else:
        harvest_records(url=url, name=name, from_date=from_date, size=size,
                        verbose=verbose)


@apiharvester.command('info')
@with_appcontext
def info():
    """List infos for tasks."""
    apis = ApiHarvestConfig.query.all()
    for api in apis:
        click.echo(api.name)
        click.echo('\tlastrun  : {0}'.format(api.lastrun))
        click.echo('\turl      : {0}'.format(api.url))
        click.echo('\tmimetype : {0}' .format(api.mimetype))
        click.echo('\tsize     : {0}' .format(api.size))
        click.echo('\tcomment  : {0}' .format(api.comment))
