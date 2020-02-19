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

import click
from flask.cli import with_appcontext

from ..documents.api import DocumentsSearch
from ..holdings.api import create_holding
from ..item_types.api import ItemTypesSearch
from ..locations.api import LocationsSearch
from ..organisations.api import Organisation
from ..utils import read_json_record


def get_documents_with_type_journal():
    """Get pids of documents with type journal."""
    document_pids = []
    es_documents = DocumentsSearch()\
        .filter('term', type="journal").source(['pid']).scan()
    return [es_document.pid for es_document in es_documents]


def get_location(library_pid):
    """Get a location pid for the given library pid.

    :param library_pid: a valid library pid.
    :returns: pid of location.
    """
    results = LocationsSearch().source(['pid'])\
        .filter('term', library__pid=library_pid)\
        .scan()
    locations = [location.pid for location in results]
    return next(iter(locations or []), None)


def get_circ_category(org_pid):
    """Get random circ category for an organisation pid."""
    results = ItemTypesSearch().source(['pid'])\
        .filter('term', organisation__pid=org_pid)\
        .scan()
    records = [record.pid for record in results]
    return next(iter(records or []), None)


def get_random_location(org_pid):
    """Return random location for an organisation pid."""
    org = Organisation.get_record_by_pid(org_pid)
    libraries = [library.pid for library in org.get_libraries()]
    return get_location(next(iter(libraries or []), None))


@click.command('create_patterns')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option('-d', '--debug', 'debug', is_flag=True, default=False)
@click.option('-l', '--lazy', 'lazy', is_flag=True, default=False)
@click.argument('infile', type=click.File('r'))
@with_appcontext
def create_patterns(infile, verbose, debug, lazy):
    """Create serials patterns for documents of type journals.

    :param infile: Json patterns file
    :param lazy: lazy reads file
    """
    click.secho('Create serials patterns:', fg='green')
    journal_pids = get_documents_with_type_journal()
    if lazy:
        # try to lazy read json file (slower, better memory management)
        data = read_json_record(infile)
    else:
        # load everything in memory (faster, bad memory management)
        data = json.load(infile)
    for record_index, record in enumerate(data):
        template_name = record.get('template_name')
        try:
            document_pid = journal_pids[record_index]
        except IndexError as error:
            break
        patterns = record.get('patterns')
        for org_pid in Organisation.get_all_pids():
            circ_category_pid = get_circ_category(org_pid)
            location_pid = get_random_location(org_pid)
            holding_pid = create_holding(
                document_pid=document_pid,
                location_pid=location_pid,
                item_type_pid=circ_category_pid,
                holdings_type='serial',
                patterns=patterns)
            click.echo(
                'ptr {template_name}: hld {holding_pid} doc {document_pid}'
                .format(
                    ptr='Pattern',
                    hld='created for holdings',
                    doc='and document',
                    template_name=template_name,
                    holding_pid=holding_pid,
                    document_pid=document_pid
                ))
        record_index = record_index + 1
