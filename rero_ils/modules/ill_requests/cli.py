# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

"""Click command-line interface for ill_request record management."""

from __future__ import absolute_import, print_function

import json
import random

import click
from flask.cli import with_appcontext

from rero_ils.modules.ill_requests.api import ILLRequest
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import get_ref_for_pid


@click.command('create_ill_requests')
@click.option('-f', '--requests_file', 'input_file', help='Request input file')
@with_appcontext
def create_ill_requests(input_file):
    """Create ILL request for each organisation."""
    locations = get_locations()
    patron_pids = {}

    with open(input_file, 'r', encoding='utf-8') as request_file:
        requests = json.load(request_file)
        for request_data in requests:
            for organisation_pid, location_pid in locations.items():
                if 'pid' in request_data:
                    del request_data['pid']
                if organisation_pid not in patron_pids:
                    patron_pids[organisation_pid] = [
                        pid for pid in Patron.get_all_pids_for_organisation(
                            organisation_pid)
                        if Patron.get_record_by_pid(pid).is_patron
                    ]
                patron_pid = random.choice(patron_pids[organisation_pid])
                request_data['patron'] = {
                    '$ref': get_ref_for_pid('patrons', patron_pid)
                }
                request_data['pickup_location'] = {
                    '$ref': get_ref_for_pid('locations', location_pid)
                }
                request = ILLRequest.create(
                    request_data,
                    dbcommit=True,
                    reindex=True
                )
                click.echo(
                    f'\tRequest: #{request.pid}  \t'
                    f'for org#{request.organisation_pid}'
                )


def get_locations():
    """Get one pickup_location for each organisation.

    :return: A dict of locations pids by organisation
    """
    location_data = {}
    for pid in Location.get_pickup_location_pids(is_ill_pickup=True):
        record = Location.get_record_by_pid(pid)
        if record.organisation_pid not in location_data:
            location_data[record.organisation_pid] = pid
    return location_data
