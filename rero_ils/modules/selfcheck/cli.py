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

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_oauth2server.cli import process_scopes, process_user

from rero_ils.modules.locations.api import search_location_by_pid

from .models import SelfcheckTerminal


@click.command('terminal_create')
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
def terminal_create(name, user, location_pid, scopes, internal,
                    access_token):
    """Create a personal OAuth token."""
    from rero_ils.modules.cli import create_personal  # avoid circular import

    location = search_location_by_pid(location_pid)
    if location:
        token = create_personal(
            name, user.id, scopes=scopes, is_internal=internal,
            access_token=access_token)
        selfcheck_terminal = SelfcheckTerminal(
            name=name,
            access_token=token.access_token,
            organisation_pid=location.organisation['pid'],
            library_pid=location.library['pid'],
            location_pid=location_pid
        )
        db.session.add(selfcheck_terminal)
        db.session.commit()
        click.secho(f'login: {name}', fg='blue')
        click.secho(f'token: {token.access_token}', fg='blue')
