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

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import json

import click
from flask.cli import with_appcontext

from ..libraries_locations.api import LibraryWithLocations
from ..locations.api import Location
from ..organisations_libraries.api import OrganisationWithLibraries


@click.command('importorganisations')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def import_organisations(infile, verbose):
    """Import organisation.

    infile: Json organisation file
    """
    click.secho(
        'Import organisations:',
        fg='green'
    )

    data = json.load(infile)
    for organisation_data in data:
        if verbose:
            click.echo('\tOrganisation: ' + organisation_data['name'])
        libraries_data = organisation_data['libraries']
        del(organisation_data['libraries'])
        organisation = OrganisationWithLibraries.create(organisation_data)
        for library_data in libraries_data:
            if verbose:
                click.echo('\t\tLibrary: ' + library_data['name'])
            locations_data = library_data['locations']
            del(library_data['locations'])
            library = LibraryWithLocations.create(
                library_data,
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
                library.add_location(location, dbcommit=True, reindex=True)
            organisation.add_library(library, dbcommit=True, reindex=True)
        organisation.dbcommit(reindex=True)
