# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

import sys

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_oauth2server.cli import process_scopes, process_user
from invenio_oauth2server.provider import get_token

from rero_ils.modules.locations.api import search_location_by_pid

from .models import SelfcheckTerminal


@click.command('create_terminal')
@click.option('-n', '--name', required=True)
@click.option(
    '-u', '--user', required=True, callback=process_user,
    help='User ID or email.')
@click.option(
    '-l', '--location-pid', required=True)
@click.option(
    '-s', '--scope', 'scopes', multiple=True, callback=process_scopes)
@click.option('-i', '--internal', is_flag=True)
@click.option(
    '-t', '--access_token', 'access_token', required=False,
    help='personalized access_token.')
@with_appcontext
def create_terminal(name, user, location_pid, scopes, internal,
                    access_token):
    """Create a personal OAuth token."""
    from rero_ils.modules.cli import create_personal  # avoid circular import

    # check if user exist:
    if not user:
        click.secho(
            f'ERROR user does not exist',
            fg='red'
        )
        sys.exit(1)
    # check if name already exist
    terminal = SelfcheckTerminal.find_terminal(name=name)
    if terminal:
        click.secho(
            f'ERROR terminal name already exist: {name}',
            fg='red'
        )
        sys.exit(1)

    location = search_location_by_pid(location_pid)
    if location:
        # try:
        token = get_token(access_token=access_token)
        if not token:
            click.secho(f'create token for: {user}', fg='blue')
            token = create_personal(
                name, user.id, scopes=scopes, is_internal=internal,
                access_token=access_token)
            access_token = token.access_token
        if access_token:
            selfcheck_terminal = SelfcheckTerminal(
                name=name,
                access_token=access_token,
                organisation_pid=location.organisation['pid'],
                library_pid=location.library['pid'],
                location_pid=location_pid
            )
            db.session.add(selfcheck_terminal)
            db.session.commit()

        click.secho(f'login: {name}', fg='green')
        click.secho(f'token: {access_token}', fg='green')


@click.command('list_terminal')
@with_appcontext
def list_terminal():
    """List all configured terminals."""
    for terminal in SelfcheckTerminal.query.order_by('id').all():
        click.echo(terminal.name)
        click.echo(f'\ttoken            : {terminal.access_token}')
        click.echo(f'\torganisation_pid : {terminal.organisation_pid}')
        click.echo(f'\tlibrary_pid      : {terminal.library_pid}')
        click.echo(f'\tlocation_pid     : {terminal.location_pid}')
        click.echo(f'\tactive           : {terminal.active}')
        click.echo(f'\tlast login       : {terminal.last_login_at}')


@click.command('update_terminal')
@click.argument('name')
@click.option('-e', '--enable', 'enable', is_flag=True, default=False)
@click.option('-d', '--disable', 'disable', is_flag=True, default=False)
@click.option('-l', '--loc-pid', 'location_pid')
@click.option('-t', '--access-token', 'access_token')
@with_appcontext
def update_terminal(name, enable, disable, location_pid, access_token):
    """Update the given terminal."""
    terminal = SelfcheckTerminal.find_terminal(name=name)
    if terminal:
        if disable and not enable:
            terminal.active = False
        if enable and not disable:
            terminal.active = True
        if location_pid:
            location = search_location_by_pid(location_pid)
            if location:
                terminal.organisation_pid = location.organisation['pid'],
                terminal.library_pid = location.library['pid'],
                terminal.location_pid = location_pid
        if access_token:
            token = get_token(access_token)
            if token:
                terminal.access_token = token.access_token
            else:
                click.secho(
                    f'WARNING token is not valid or does not exist : '
                    f'{access_token}',
                    fg='yellow'
                )
        db.session.merge(terminal)
        db.session.commit()
        click.secho(f'{name} updated', fg='green')
