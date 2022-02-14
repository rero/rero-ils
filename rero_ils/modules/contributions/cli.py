# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2020 UCLouvain
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

"""Click command-line utilities."""

from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext

from .tasks import update_contributions as task_update_contributions


@click.group()
def contribution():
    """Contribution management commands."""


@contribution.command()
@click.option('-p', '--pid', multiple=True)
@click.option('-c', '--dbcommit', is_flag=True, default=False)
@click.option('-r', '--reindex', is_flag=True, default=False)
@click.option('-t', '--timestamp', is_flag=True, default=False)
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def update_contributions(pid, dbcommit, reindex, timestamp, verbose):
    """Update contributions.

    :param pids: contribution pids to update, default ALL.
    :param dbcommit: if True call dbcommit, make the change effective in db.
    :param reindex: reindex the record.
    :param verbose: verbose print.
    :param timestamp: create timestamp.
    """
    click.secho('Update contributions', fg='green')
    msg = task_update_contributions(pids=pid, dbcommit=dbcommit,
                                    reindex=reindex, timestamp=timestamp,
                                    verbose=verbose)
    if verbose:
        for action, count in msg.items():
            click.echo(f'{action}: {count}')
