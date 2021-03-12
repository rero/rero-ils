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

"""Click command-line interface for notifications."""

from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext

from .tasks import process_notifications


@click.group()
def notifications():
    """Notification management commands."""


@notifications.command('process')
@click.option('--delayed', '-d', is_flag=True, default=False,
              help='Run indexing in background.')
@click.option('-v', '--verbose', is_flag=True, default=False,
              help='Verbose output')
@with_appcontext
def process(delayed, verbose):
    """Process notifications."""
    click.secho('Process notifications:', fg='green')
    if delayed:
        uid = process_notifications.delay(verbose=verbose)
        msg = f'Started task: {uid}'
    else:
        msg = process_notifications(verbose=verbose)
    click.echo(msg)
