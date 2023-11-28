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

from .replace import ReplaceIdentifiedBy
from .sync import SyncEntity


@click.group()
def entity():
    """Entity management commands."""


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
    sync_entity = SyncEntity(
        dry_run=dry_run, verbose=verbose, log_dir=log_dir,
        from_last_date=from_last_date)
    if verbose:
        sync_entity.sync(query, from_date)
    else:
        sync_entity.start_sync()
        pids, total = sync_entity.get_entities_pids(query, from_date)
        if in_memory:
            pids = list(pids)
        n_updated = 0
        doc_updated = set()
        err_pids = []
        with click.progressbar(pids, length=total) as bar:
            for pid in bar:
                current_doc_updated, updated, error = sync_entity.sync_record(
                    pid)
                doc_updated.update(current_doc_updated)
                if updated:
                    n_updated += 1
                if error:
                    err_pids.append(pid)
        n_doc_updated = len(doc_updated)
        sync_entity.end_sync(n_doc_updated, n_updated, err_pids)
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
    sync_entity = SyncEntity(dry_run=dry_run, verbose=verbose, log_dir=log_dir)
    if verbose:
        sync_entity.remove_unused(query)
    else:
        sync_entity.start_clean()
        pids, total = sync_entity.get_entities_pids(query)
        n_removed = 0
        err_pids = []
        with click.progressbar(pids, length=total) as bar:
            for pid in bar:
                try:
                    n_removed += int(sync_entity.remove_unused_record(pid))
                except Exception:
                    err_pids.append(pid)

        click.secho(f'{n_removed} removed MEF records', fg='green')
        if err_pids:
            click.secho(f'ERROR: MEF pids: {err_pids}', fg='red')


@entity.command()
@click.option('-c', '--clear', is_flag=True, default=False)
@click.option('-v', '--verbose', count=True, default=0)
@with_appcontext
def sync_errors(clear, verbose):
    """Removes errors in the cache information."""
    errors = SyncEntity.get_errors()
    if verbose:
        click.echo(f'Errors MEF pids: {errors}')
    if clear:
        SyncEntity.clear_errors()
        click.secho(f'Removed {len(errors)} errors', fg='yellow')


@entity.command('replace-identified-by')
@click.option('-f', '--field', multiple=True, default=None)
@click.option('-n', '--dry-run', is_flag=True, default=False)
@click.option('-v', '--verbose', count=True, default=0)
@click.option('-l', '--log-dir', default=None)
@with_appcontext
def replace_identified_by_cli(field, dry_run, verbose, log_dir):
    """Replace identifiedBy with $ref."""
    for parent in field or ReplaceIdentifiedBy.fields:
        replace_identified_by = ReplaceIdentifiedBy(
            field=parent,
            verbose=verbose,
            dry_run=dry_run,
            log_dir=log_dir
        )
        changed, not_found, rero_only = replace_identified_by.run()
        click.secho(
            f'{parent:<12} | Changed: {changed} | '
            f'Not found: {not_found} | '
            f'RERO only: {rero_only}',
            fg='green'
        )
        if verbose:
            if replace_identified_by._error_count(
                    replace_identified_by.not_found):
                click.secho('Not found:', fg='yellow')
                for etype, values in replace_identified_by.not_found.items():
                    for pid, data in values.items():
                        click.echo(f'\t{etype} {pid}: {data}')
            if replace_identified_by._error_count(
                    replace_identified_by.rero_only):
                click.secho('RERO only:', fg='yellow')
                for etype, values in replace_identified_by.rero_only.items():
                    for pid, data in values.items():
                        click.echo(f'\t{pid}: {data}')
