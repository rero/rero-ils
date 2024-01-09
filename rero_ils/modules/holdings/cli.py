# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.holdings.api import Holding, create_holding
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.items.api import ItemIssue
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.items.tasks import process_late_issues
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.utils import read_json_record


def get_document_pid_by_rero_number(rero_control_number):
    """Get pid of document by rero control number."""
    es_documents = DocumentsSearch()\
        .filter('term', identifiedBy__value__raw=rero_control_number)\
        .source('pid')
    documents = [document.pid for document in es_documents.scan()]
    return documents[0] if documents else None


def get_circ_category(org_pid):
    """Get a random standard circulation category for an organisation pid."""
    results = ItemTypesSearch()\
        .filter('term', organisation__pid=org_pid)\
        .filter('term', type='standard') \
        .source('pid')
    records = [record.pid for record in results.scan()]
    return next(iter(records or []), None)


def get_random_location_pid(org_pid):
    """Return random location for an organisation pid."""
    results = LocationsSearch() \
        .filter('term', organisation__pid=org_pid) \
        .source('pid')
    locations = [location.pid for location in results.scan()]
    return next(iter(locations or []), None)


def get_random_vendor(org_pid):
    """Return random vendor for an organisation pid."""
    org = Organisation.get_record_by_pid(org_pid)
    if vendors := [vendor.pid for vendor in org.get_vendors()]:
        return next(iter(random.choices(vendors) or []), None)


def create_issues_from_holding(holding, min=3, max=9):
    """Receive randomly new issues.

    :param holding: the holding record.
    :param min, max: the min and max range to randomly create number of issues.
    """
    count = 0
    for _ in range(random.randint(min, max)):
        # prepare some fields for the issue to ensure a variable recv dates.
        issue_display, expected_date = holding._get_next_issue_display_text(
                    holding.get('patterns'))
        item = {
            'issue': {
                'received_date': expected_date,
            },
        }
        holding.create_regular_issue(
            status=ItemIssueStatus.RECEIVED,
            item=item,
            dbcommit=True,
            reindex=True
        )
        holding = Holding.get_record_by_pid(holding.pid)
        count += 1
    return count


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
    data = read_json_record(infile) if lazy else json.load(infile)
    for record_index, record in enumerate(data):
        template_name = record.get('template_name')
        if rero_control_number := record.get('rero_control_number'):
            document_pid = get_document_pid_by_rero_number(rero_control_number)
        else:
            try:
                document_pid = journal_pids[record_index]
            except IndexError as error:
                break
        patterns = record.get('patterns')
        enumerationAndChronology = record.get('enumerationAndChronology')
        supplementaryContent = record.get('supplementaryContent')
        index = record.get('index')
        missing_issues = record.get('missing_issues')
        notes = record.get('notes')
        call_number = record.get('call_number')
        second_call_number = record.get('second_call_number')
        acquisition_status = record.get('acquisition_status')
        acquisition_method = record.get('acquisition_method')
        general_retention_policy = record.get('general_retention_policy')
        composite_copy_report = record.get('composite_copy_report')
        issue_binding = record.get('issue_binding')
        completeness = record.get('completeness')
        acquisition_expected_end_date = record.get(
            'acquisition_expected_end_date')
        for org_pid in Organisation.get_all_pids():
            circ_category_pid = get_circ_category(org_pid)
            location_pid = get_random_location_pid(org_pid)
            vendor_pid = get_random_vendor(org_pid)
            holdings_record = create_holding(
                document_pid=document_pid,
                location_pid=location_pid,
                item_type_pid=circ_category_pid,
                holdings_type='serial',
                enumerationAndChronology=enumerationAndChronology,
                supplementaryContent=supplementaryContent,
                index=index,
                missing_issues=missing_issues,
                notes=notes,
                acquisition_status=acquisition_status,
                acquisition_method=acquisition_method,
                acquisition_expected_end_date=acquisition_expected_end_date,
                composite_copy_report=composite_copy_report,
                general_retention_policy=general_retention_policy,
                issue_binding=issue_binding,
                completeness=completeness,
                call_number=call_number,
                second_call_number=second_call_number,
                vendor_pid=vendor_pid,
                patterns=patterns)
            # create minimum 3 and max 9 received issues for this holdings
            count = create_issues_from_holding(holding=holdings_record,
                                               min=3, max=9)
            click.echo(
                f'Pattern <{template_name}> created {count} '
                f'received issues for holdings:  {holdings_record.pid} '
                f'and document: {document_pid}'
            )
        record_index = record_index + 1
    # create some late issues.
    process_late_issues(dbcommit=True, reindex=True)
    # make late issues ready for a claim
    for issue in ItemIssue.get_issues_by_status(status=ItemIssueStatus.LATE):
        issue['issue']['status_date'] = \
            (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        issue.update(issue, dbcommit=True, reindex=True)
