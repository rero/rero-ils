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

from ..documents.tasks import \
    replace_idby_contribution as task_replace_idby_contribution
from ..documents.tasks import \
    replace_idby_subjects as task_replace_idby_subjects


@click.group()
def contribution():
    """Contribution management commands."""


def do_replace_idby(name, replace_class, verbose, debug, details, **kwargs):
    """Find and replace identifiedBy."""
    click.secho(f'Find and replace identifiedBy {name}.', fg='green')
    found, exists, deleted, no_data, no_mef = replace_class(
        verbose=verbose, details=details, debug=debug, **kwargs)
    click.echo(f'Found: {found} | Exists: {exists} | Deleted: {deleted} | '
               f'No Data: {no_data} | No MEF: {no_mef}')


@contribution.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-D', '--details', is_flag=True, default=False)
@with_appcontext
def replace_idby_contribution(verbose, debug, details):
    """Find and replace identifiedBy contributions."""
    do_replace_idby(
        name='contribution',
        replace_class=task_replace_idby_contribution,
        verbose=verbose,
        details=details,
        debug=debug
    )


@contribution.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-D', '--details', is_flag=True, default=False)
@with_appcontext
def replace_idby_subjects(verbose, debug, details):
    """Find and replace identifiedBy subjects."""
    do_replace_idby(
        name='subjects',
        replace_class=task_replace_idby_subjects,
        verbose=verbose,
        details=details,
        debug=debug
    )


@contribution.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-D', '--details', is_flag=True, default=False)
@with_appcontext
def replace_idby_subjects_imported(verbose, debug, details):
    """Find and replace identifiedBy subjects imported."""
    do_replace_idby(
        name='subjects_imported',
        replace_class=task_replace_idby_subjects,
        verbose=verbose,
        details=details,
        debug=debug,
        subjects='subjects_imported'
    )
