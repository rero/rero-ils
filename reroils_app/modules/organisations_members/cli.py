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
from flask.cli import with_appcontext

from ..locations.api import Location
from ..members_locations.api import MemberWithLocations
from ..organisations_members.api import OrganisationWithMembers


@click.command('importorganisations')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', 'Json organisation file', type=click.File('r'))
@with_appcontext
def import_organisations(infile, verbose):
    """Import organisation."""
    click.secho(
        'Import organisations:',
        fg='green'
    )

    data = json.load(infile)
    for organisation_data in data:
        if verbose:
            click.echo('\tOrganisation: ' + organisation_data['name'])
        members_data = organisation_data['members']
        del(organisation_data['members'])
        organisation = OrganisationWithMembers.create(organisation_data)
        for member_data in members_data:
            if verbose:
                click.echo('\t\tMember: ' + member_data['name'])
            locations_data = member_data['locations']
            del(member_data['locations'])
            member = MemberWithLocations.create(
                member_data,
                dbcommit=True,
                reindex=True
            )
            for location_data in locations_data:
                if verbose:
                    click.echo('\t\t\tLocation: ' + location_data['name'])
                location = Location.create(
                    location_data,
                    dbcommit=True,
                    reindex=True
                )
                member.add_location(location, dbcommit=True, reindex=True)
            organisation.add_member(member, dbcommit=True, reindex=True)
        organisation.dbcommit(reindex=True)
