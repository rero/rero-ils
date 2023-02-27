# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

from rero_ils.modules.documents.tasks import \
    replace_idby_contribution as task_replace_idby_contribution
from rero_ils.modules.documents.tasks import \
    replace_idby_subjects as task_replace_idby_subjects

from .sync import SyncAgent


@click.group()
def entity():
    """Entity management commands."""


def _do_replace_idby(name, replace_class, verbose, debug, details, **kwargs):
    """Find and replace identifiedBy."""
    click.secho(f'Find and replace identifiedBy {name}.', fg='green')
    found, exists, deleted, no_data, no_mef = replace_class(
        verbose=verbose,
        details=details,
        debug=debug,
        **kwargs
    )
    click.echo(f'Found: {found} | Exists: {exists} | Deleted: {deleted} | '
               f'No Data: {no_data} | No MEF: {no_mef}')


@entity.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-D', '--details', is_flag=True, default=False)
@with_appcontext
def replace_idby_contribution(verbose, debug, details):
    """Find and replace identifiedBy contributions."""
    _do_replace_idby(
        name='contribution',
        replace_class=task_replace_idby_contribution,
        verbose=verbose,
        details=details,
        debug=debug
    )


@entity.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-D', '--details', is_flag=True, default=False)
@with_appcontext
def replace_idby_subjects(verbose, debug, details):
    """Find and replace identifiedBy subjects."""
    _do_replace_idby(
        name='subjects',
        replace_class=task_replace_idby_subjects,
        verbose=verbose,
        details=details,
        debug=debug
    )


@entity.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-d', '--debug', is_flag=True, default=False)
@click.option('-D', '--details', is_flag=True, default=False)
@with_appcontext
def replace_idby_subjects_imported(verbose, debug, details):
    """Find and replace identifiedBy subjects imported."""
    _do_replace_idby(
        name='subjects_imported',
        replace_class=task_replace_idby_subjects,
        verbose=verbose,
        details=details,
        debug=debug,
        subjects='subjects_imported'
    )


@entity.command()
@click.option('-q', '--query', default='*')
@click.option('-n', '--dry-run', is_flag=True, default=False)
@click.option('-d', '--from-last-date', is_flag=True, default=False)
@click.option('-v', '--verbose', count=True, default=0)
@click.option('-l', '--log-dir', default=None)
@click.option('-f', '--from-date',
              type=click.DateTime(formats=["%Y-%m-%d"]), default=None)
@click.option('-m', '--in-memory', is_flag=True, default=False)
@with_appcontext
def sync(query, dry_run, from_last_date, verbose, log_dir, from_date,
         in_memory):
    """Updated the MEF records and the linked documents."""
    a = SyncAgent(
        dry_run=dry_run, verbose=verbose, log_dir=log_dir,
        from_last_date=from_last_date)
    if verbose:
        a.sync(query, from_date)
    else:
        a.start_sync()
        pids, total = a.get_entities_pids(query, from_date)
        if in_memory:
            pids = list(pids)
        n_updated = 0
        doc_updated = set()
        err_pids = []
        with click.progressbar(pids, length=total) as bar:
            for pid in bar:
                current_doc_updated, updated, error = a.sync_record(pid)
                doc_updated.update(current_doc_updated)
                if updated:
                    n_updated += 1
                if error:
                    err_pids.append(pid)
        n_doc_updated = len(doc_updated)
        a.end_sync(n_doc_updated, n_updated, err_pids)
        if err_pids:
            click.secho(f'ERROR: MEF pids: {err_pids}', fg='red')


@entity.command()
@click.option('-q', '--query', default='*')
@click.option('-n', '--dry-run', is_flag=True, default=False)
@click.option('-v', '--verbose', count=True, default=0)
@click.option('-l', '--log-dir', default=None)
@with_appcontext
def clean(query, dry_run, verbose, log_dir):
    """Removes MEF records that are not linked to documents."""
    a = SyncAgent(dry_run=dry_run, verbose=verbose, log_dir=log_dir)
    if verbose:
        a.remove_unused(query)
    else:
        a.start_clean()
        pids, total = a.get_entities_pids(query)
        n_removed = 0
        err_pids = []
        with click.progressbar(pids, length=total) as bar:
            for pid in bar:
                updated, error = a.remove_unused_record(pid)
                if updated:
                    n_removed += 1
                if error:
                    err_pids.append(pid)

        click.secho(f'{n_removed} removed MEF records', fg='green')
        if err_pids:
            click.secho(f'ERROR: MEF pids: {err_pids}', fg='red')


@entity.command()
@click.option('-c', '--clear', is_flag=True, default=False)
@with_appcontext
def sync_errors(clear):
    """Removes errors in the cache information."""
    errors = SyncAgent.get_errors()
    if clear:
        SyncAgent.clear_errors()
        click.secho(f'Removed {len(errors)} errors', fg='yellow')
