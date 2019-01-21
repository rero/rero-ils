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

"""Click command-line utilities."""

from __future__ import absolute_import, print_function

import json
import os
from collections import OrderedDict
from glob import glob

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.cli import commit, users
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from werkzeug.local import LocalProxy

from .items.cli import create_items, reindex_items
from .loans.cli import create_loans
from .patrons.cli import import_users

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.group()
def fixtures():
    """Fixtures management commands."""


fixtures.add_command(import_users)
fixtures.add_command(create_items)
fixtures.add_command(reindex_items)
fixtures.add_command(create_loans)


@users.command('confirm')
@click.argument('user')
@with_appcontext
@commit
def manual_confirm_user(user):
    """Confirm a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError('ERROR: User not found.')
    if confirm_user(user_obj):
        click.secho('User "%s" has been confirmed.' % user, fg='green')
    else:
        click.secho('User "%s" was already confirmed.' % user, fg='yellow')


@click.group()
def utils():
    """Misc management commands."""


@utils.command('show')
@click.argument('pid_value', nargs=1)
@click.option('-t', '--pid-type', 'pid-type, default(document_id)',
              default='document_id')
@with_appcontext
def show(pid_value, pid_type):
    """Show records."""
    record = PersistentIdentifier.query.filter_by(pid_type=pid_type,
                                                  pid_value=pid_value).first()
    recitem = Record.get_record(record.object_uuid)
    click.echo(json.dumps(recitem.dumps(), indent=2))


@utils.command('check_json')
@click.argument('paths', nargs=-1)
@click.option(
    '-r', '--replace', 'replace', is_flag=True, default=False,
    help='change file in place default=False'
)
@click.option(
    '-s', '--sort-keys', 'sort_keys', is_flag=True, default=False,
    help='order keys during replacement default=False'
)
@click.option(
    '-i', '--indent', 'indent', type=click.INT, default=2,
    help='intent default=2'
)
def check_json(paths, replace, indent, sort_keys):
    """Check json files."""
    files_list = []
    for path in paths:
        if os.path.isfile(path):
            files_list.append(path)
        elif os.path.isdir(path):
            files_list = files_list + glob(os.path.join(path, '**/*.json'),
                                           recursive=True)
    if not paths:
        files_list = glob('**/*.json', recursive=True)
    tot_error_cnt = 0
    for path_file in files_list:
        error_cnt = 0
        try:
            fname = path_file
            with open(fname, 'r') as opened_file:
                json_orig = opened_file.read().rstrip()
                opened_file.seek(0)
                json_file = json.load(opened_file,
                                      object_pairs_hook=OrderedDict)
            json_dump = json.dumps(json_file, indent=indent).rstrip()
            if json_dump != json_orig:
                error_cnt = 1
            click.echo(fname + ': ', nl=False)
            if replace:
                with open(fname, 'w') as opened_file:
                    opened_file.write(json.dumps(json_file,
                                                 indent=indent,
                                                 sort_keys=sort_keys))
                click.secho('File replaced', fg='yellow')
            else:
                if error_cnt == 0:
                    click.secho('Well indented', fg='green')
                else:
                    click.secho('Bad indentation', fg='red')
        except ValueError as e:
            click.echo(fname + ': ', nl=False)
            click.secho('Invalid JSON', fg='red', nl=False)
            click.echo(' -- ' + e.msg)
            error_cnt = 1

        tot_error_cnt += error_cnt
    return tot_error_cnt


@utils.command('schedules')
@with_appcontext
def schedules():
    """List harvesting schedules."""
    celery_ext = current_app.extensions.get('invenio-celery')
    for key, value in celery_ext.celery.conf.beat_schedule.items():
        click.echo(key + '\t', nl=False)
        click.echo(value)
