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

"""Click command-line interface for item record management."""

from __future__ import absolute_import, print_function

import json
import random

import click
from flask.cli import with_appcontext

from ..documents.api import Document, DocumentsSearch
from ..holdings.api import Holding, create_holding
from ..item_types.api import ItemTypesSearch
from ..locations.api import LocationsSearch
from ..organisations.api import Organisation
from ..utils import read_json_record


def get_document_pid_by_rero_number(rero_control_number):
    """Get pid of document by rero control number."""
    es_documents = DocumentsSearch()\
        .filter('term', identifiedBy__value=rero_control_number).source(
            ['pid']).scan()
    documents = [document.pid for document in es_documents]
    return documents[0] if documents else None


def get_location(library_pid):
    """Get a location pid for the given library pid.

    :param library_pid: a valid library pid.
    :return: pid of location.
    """
    results = LocationsSearch().source(['pid'])\
        .filter('term', library__pid=library_pid)\
        .scan()
    locations = [location.pid for location in results]
    return next(iter(locations or []), None)


def get_circ_category(org_pid):
    """Get a random standard circulation category for an organisation pid."""
    results = ItemTypesSearch().source(['pid'])\
        .filter('term', organisation__pid=org_pid)\
        .filter('term', type='standard')\
        .scan()
    records = [record.pid for record in results]
    return next(iter(records or []), None)


def get_random_location(org_pid):
    """Return random location for an organisation pid."""
    org = Organisation.get_record_by_pid(org_pid)
    libraries = [library.pid for library in org.get_libraries()]
    return get_location(next(iter(libraries or []), None))


def create_issues_from_holding(holding, min=3, max=9):
    """Receive randomly new issues.

    :param holding: the holding record.
    :param min, max: the min and max range to randomly create number of issues.
    """
    for issue_number in range(0, random.randint(min, max)):
        # prepare some fields for the issue to ensure a variable recv dates.
        issue_display, expected_date = holding._get_next_issue_display_text(
                    holding.get('patterns'))
        item = {
            'issue': {
                'received_date': expected_date,
            },
        }
        holding.receive_regular_issue(item=item, dbcommit=True, reindex=True)
        holding = Holding.get_record_by_pid(holding.pid)


@click.command('create_patterns')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def create_patterns(infile, verbose, debug, lazy):
    """Create serials patterns for Serial mode of issuance documents.

    :param infile: Json patterns file
    :param lazy: lazy reads file
    """
    click.secho('Create serials patterns:', fg='green')
    journal_pids = Document.get_all_serial_pids()
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        data = json.load(infile)
    for record_index, record in enumerate(data):
        template_name = record.get('template_name')
        rero_control_number = record.get('rero_control_number')
        if rero_control_number:
            document_pid = get_document_pid_by_rero_number(rero_control_number)
        else:
            try:
                document_pid = journal_pids[record_index]
            except IndexError as error:
                break
        patterns = record.get('patterns')
        for org_pid in Organisation.get_all_pids():
            circ_category_pid = get_circ_category(org_pid)
            location_pid = get_random_location(org_pid)
            holdings_record = create_holding(
                document_pid=document_pid,
                location_pid=location_pid,
                item_type_pid=circ_category_pid,
                holdings_type='serial',
                patterns=patterns)
            # create minimum 3 and max 9 received issues for this holdings
            create_issues_from_holding(holdings_record)
            text = '> created (& between 3 and 9 rcvd issues) for holdings_pid'
            click.echo(
                '{ptr_str}{template}{hld_str} {holding} {doc_str} {document}'
                .format(
                    ptr_str='Pattern <',
                    hld_str=text,
                    doc_str='and document_pid',
                    template=template_name,
                    holding=holdings_record.pid,
                    document=document_pid
                ))
        record_index = record_index + 1
