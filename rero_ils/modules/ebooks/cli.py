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

"""Click command-line interface for ebook record management."""

from __future__ import absolute_import, print_function

import click
import yaml
from flask.cli import with_appcontext
from invenio_oaiharvester.cli import oaiharvester
from invenio_oaiharvester.models import OAIHarvestConfig

from .utils import add_oai_source


@oaiharvester.command('addsource')
@click.argument('name')
@click.argument('baseurl')
@click.option('-m', '--metadataprefix', default='marc21',
              help='The prefix for the metadata')
@click.option('-s', '--setspecs', default='',
              help='The ‘set’ criteria for the harvesting')
@click.option('-c', '--comment', default='',
              help='Comment')
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def add_oai_source_config(name, baseurl, metadataprefix, setspecs, comment,
                          update):
    """Add OAIHarvestConfig."""
    click.echo(f'Add OAIHarvestConfig: {name} ', nl=False)
    msg = add_oai_source(
        name=name,
        baseurl=baseurl,
        metadataprefix=metadataprefix,
        setspecs=setspecs,
        comment=comment,
        update=update
    )
    click.echo(msg)


@oaiharvester.command('initconfig')
@click.argument('configfile', type=click.File('rb'))
@click.option(
    '-u', '--update', is_flag=True, default=False, help='Update config'
)
@with_appcontext
def init_oai_harvest_config(configfile, update):
    """Init OAIHarvestConfig."""
    configs = yaml.load(configfile, Loader=yaml.FullLoader)
    for name, values in sorted(configs.items()):
        baseurl = values['baseurl']
        metadataprefix = values.get('metadataprefix', 'marc21')
        setspecs = values.get('setspecs', '')
        comment = values.get('comment', '')
        click.echo(f'Add OAIHarvestConfig: {name} {baseurl} ', nl=False)
        msg = add_oai_source(
            name=name,
            baseurl=baseurl,
            metadataprefix=metadataprefix,
            setspecs=setspecs,
            comment=comment,
            update=update
        )
        click.echo(msg)


@oaiharvester.command('info')
@with_appcontext
def info():
    """List infos for tasks."""
    oais = OAIHarvestConfig.query.all()
    for oai in oais:
        click.echo(oai.name)
        click.echo('\tlastrun       : ', nl=False)
        click.echo(oai.lastrun)
        click.echo('\tbaseurl       : ' + oai.baseurl)
        click.echo('\tmetadataprefix: ' + oai.metadataprefix)
        click.echo('\tcomment       : ' + oai.comment)
        click.echo('\tsetspecs      : ' + oai.setspecs)
