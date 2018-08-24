# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import json

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_security.confirmable import confirm_user
from invenio_accounts.ext import hash_password
from werkzeug.local import LocalProxy

from ..patrons.api import Patron

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('importusers')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', 'Json patron file', type=click.File('r'))
@with_appcontext
def import_users(infile, verbose):
    """Import users."""
    click.secho('Import users:', fg='green')

    data = json.load(infile)
    for patron_data in data:
        email = patron_data.get('email')
        if email is None:
            click.secho('\tUser email not defined!', fg='red')
        else:
            # create User
            password = patron_data.get('password', '123456')
            del(patron_data['password'])
            patron = Patron.get_patron_by_email(email)
            if patron:
                click.secho('\tUser exist: ' + email, fg='yellow')
            else:
                if verbose:
                    click.echo('\tUser: ' + email)
                patron = Patron.create(
                    patron_data,
                    dbcommit=True,
                    reindex=True
                )

                # create user
                user = datastore.find_user(email=email)
                confirm = False
                if user:
                    click.secho('\tUser exist: ' + email, fg='yellow')
                else:
                    pwd = hash_password(password)

                    datastore.create_user(
                        email=email,
                        password=pwd
                    )
                    datastore.commit()
                    user = datastore.find_user(email=email)
                    confirm = confirm_user(user)
                    datastore.commit()
                    if not confirm:
                        click.secho(
                            '\tUser not confirmed!' + email,
                            fg='yellow'
                        )
                    # else:
                    #     click.secho('\tUser confirmed!', fg='green')
                patron = Patron(patron, model=patron.model)
                if patron_data.get('is_patron', False):
                    patron.add_role(role_name='patrons')

                if patron_data.get('is_staff', False):
                    patron.add_role(role_name='staff')
                    # TODO: staff role
                    patron.add_role(role_name='cataloguer')
                patron.reindex()
