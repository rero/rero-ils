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
from invenio_userprofiles.models import UserProfile
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.local import LocalProxy

from ..patrons.api import Patron

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('import_users')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-p', '--password', 'password', default='123456')
@click.argument('infile', type=click.File('r'))
@with_appcontext
def import_users(infile, verbose, password):
    """Import users.

    :param verbose: this function will be verbose.
    :param password: the password to use for user by default.
    :param infile: Json user file.
    """
    click.secho('Import users:', fg='green')

    data = json.load(infile)
    for patron_data in data:
        email = patron_data.get('email')
        password = patron_data.get('password', password)
        username = patron_data['username']
        if email is None:
            click.secho('\tUser {username} do not have email!'.format(
                username=username), fg='yellow')
        if password:
            patron_data.pop('password', None)
        # do nothing if the patron alredy exists
        patron = Patron.get_patron_by_username(username)
        if patron:
            click.secho('\tPatron already exist: {username}'.format(
                username=username), fg='yellow')
            continue

        if verbose:
            click.secho('\tCreating user: {username}'.format(
                username=username), fg='green')
            try:
                profile = UserProfile.get_by_username(username)
                click.secho('\tUser already exist: {username}'.format(
                    username=username), fg='yellow')
            except NoResultFound:
                pass
        # patron creation
        patron = Patron.create(
            patron_data,
            dbcommit=False,
            reindex=False,
            email_notification=False
        )
        user = patron.user
        user.password = hash_password(password)
        user.active = True
        db.session.merge(user)
        db.session.commit()
        confirm_user(user)
        patron.reindex()
