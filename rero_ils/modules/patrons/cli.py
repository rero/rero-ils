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

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import json
import os
import sys
import traceback

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.ext import hash_password
from invenio_db import db
from invenio_userprofiles.models import UserProfile
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.local import LocalProxy

from .api import create_patron_from_data
from ..patrons.api import Patron, PatronProvider
from ..providers import append_fixtures_new_identifiers
from ..utils import read_json_record

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('import_users')
@click.option('-a', '--append', 'append', is_flag=True, default=False)
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--password', 'password', default='123456')
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.option('-o', '--dont-stop', 'dont_stop_on_error',
              is_flag=True, default=False)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'), default=sys.stdin)
@with_appcontext
def import_users(infile, append, verbose, password, lazy, dont_stop_on_error,
                 debug):
    """Import users.

    :param verbose: this function will be verbose.
    :param password: the password to use for user by default.
    :param lazy: lazy reads file
    :param dont_stop_on_error: don't stop on error
    :param infile: Json user file.
    """
    click.secho('Import users:', fg='green')

    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        data = json.load(infile)
    pids = []
    error_records = []
    for count, patron_data in enumerate(data, 1):
        email = patron_data.get('email')
        password = patron_data.get('password', password)
        username = patron_data['username']
        if email is None:
            click.secho(
                '{count: <8} User {username} do not have email!'.format(
                    count=count,
                    username=username
                ), fg='yellow')
        if password:
            patron_data.pop('password', None)
        # do nothing if the patron already exists
        patron = Patron.get_patron_by_username(username)
        if patron:
            click.secho('{count: <8} Patron already exist: {username}'.format(
                count=count,
                username=username), fg='yellow')
            continue

        if verbose:
            click.secho('{count: <8} Creating user: {username}'.format(
                count=count,
                username=username))
            try:
                profile = UserProfile.get_by_username(username)
                click.secho(
                    '{count: <8} User already exist: {username}'.format(
                        count=count,
                        username=username
                    ), fg='red')
                continue
            except NoResultFound:
                pass
        try:
            # patron creation
            patron = create_patron_from_data(
                data=patron_data,
                dbcommit=False,
                reindex=False
            )
            user = patron.user
            user.password = hash_password(password)
            user.active = True
            db.session.merge(user)
            db.session.commit()
            confirm_user(user)
            patron.reindex()
            pids.append(patron.pid)
        except Exception as err:
            error_records.append(data)
            click.secho(
                '{count: <8} User create error: {err}'.format(
                    count=count,
                    err=err
                ),
                fg='red'
            )
            if debug:
                traceback.print_exc()
            if not dont_stop_on_error:
                sys.exit(1)
            if debug:
                traceback.print_exc()
            if not dont_stop_on_error:
                sys.exit(1)
    if append:
        click.secho(f'Append fixtures new identifiers: {len(pids)}')
        identifier = Patron.provider.identifier
        try:
            append_fixtures_new_identifiers(
                identifier,
                sorted(pids, key=lambda x: int(x)),
                PatronProvider.pid_type
            )
        except Exception as err:
            click.secho(
                f'ERROR append fixtures new identifiers: {err}',
                fg='red'
            )
    if error_records:
        name, ext = os.path.splitext(infile.name)
        err_file_name = f'{name}_errors{ext}'
        click.secho(f'Write error file: {err_file_name}')
        with open(err_file_name, 'w') as error_file:
            error_file.write('[\n')
            for error_record in error_records:
                for line in json.dumps(error_record, indent=2).split('\n'):
                    error_file.write('  ' + line + '\n')
            error_file.write(']')
