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

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.ext import hash_password
from invenio_db import db
from werkzeug.local import LocalProxy

from ..patrons.api import Patron

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('import_users')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--password', 'password', default='123456')
@click.option('-r', '--reindex', 'reindex', is_flag=True, default=False)
@click.option('-c', '--dbcommit', 'dbcommit', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def import_users(infile, verbose, password, dbcommit, reindex):
    """Import users.

    :param verbose: this function will be verbose.
    :param password: the password to use for user by default.
    :param infile: Json user file.
    """
    click.secho('Import users:', fg='green')

    data = json.load(infile)
    for patron_data in data:
        email = patron_data.get('email')
        if email is None:
            click.secho('\tUser email not defined!', fg='red')
        else:
            # create User
            password = patron_data.get('password', password)
            patron_data.pop('password', None)
            patron = Patron.get_patron_by_email(email)
            if patron:
                click.secho('\tUser exist: ' + email, fg='yellow')
            else:
                if verbose:
                    click.echo('\tUser: ' + email)

                # create user
                user = datastore.find_user(email=email)
                if user:
                    click.secho('\tUser exist: ' + email, fg='yellow')
                else:
                    patron = Patron.create(
                        patron_data,
                        dbcommit=False,
                        reindex=False,
                        email_notification=False
                    )
                    patron.reindex()
                    user = patron.user
                user.password = hash_password(password)
                user.active = True
                db.session.merge(user)
                db.session.commit()
                confirm_user(user)
