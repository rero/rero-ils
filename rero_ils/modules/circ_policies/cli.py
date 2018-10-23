# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
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

"""Click command-line interface for circ_policies record management."""

from __future__ import absolute_import, print_function

import json

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.circ_policies.utils import clean_circ_policy_fields
from rero_ils.modules.errors import OrganisationDoesNotExist, \
    PolicyNameAlreadyExists

datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.command('importcircpolicies')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def import_circ_policies(infile, verbose):
    """Create circulation policies.

    infile: Json circulation policies file
    """
    click.secho('Creating circulation policies:', fg='green')
    data = json.load(infile)
    for circ_policy in data:
        message = ''
        circ_policy = clean_circ_policy_fields(circ_policy)
        try:
            record = CircPolicy.create(
                circ_policy, dbcommit=True, reindex=True
            )
            message = '\t created circ policy | pid : {0} {1}: {2}'.format(
                record['pid'], circ_policy['name'], circ_policy['description']
            )
            color = 'green'
        except OrganisationDoesNotExist:
            message = '\t Error: Organisation pid {0} does not exist'\
                .format(circ_policy['organisation_pid'])
            color = 'red'
        except PolicyNameAlreadyExists:
            message = '\t Error: circ policy name already exists: {0}'\
                .format(circ_policy['name'])
            color = 'red'
        click.secho(message, fg=color, err=False)
