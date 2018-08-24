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

import datetime
import random
from random import randint

import click
import pytz
from flask.cli import with_appcontext
from invenio_indexer.api import RecordIndexer

from reroils_app.modules.items.api import Item
from reroils_app.modules.locations.api import Location
from reroils_app.modules.members.api import Member
from reroils_app.modules.patrons.api import Patron

from .api import DocumentsWithItems


@click.command('createitems')
@click.option('-v', '--verbose', 'verbose', is_flag=True, default=False)
@click.option(
    '-c', '--count', 'count', type=click.INT, default=-1,
    help='default=for all records'
)
@click.option(
    '-i', '--itemscount', 'itemscount', type=click.INT, default=5,
    help='default=5'
)
@click.option(
    '-m', '--missing', 'missing', type=click.INT, default=5,
    help='default=10'
)
@click.option(
    '-R', '--reindex', 'reindex', is_flag=True, default=False
)
@with_appcontext
def create_items(verbose, count, itemscount, missing,
                 reindex):
    """Create circulation items."""
    uids = DocumentsWithItems.get_all_ids()

    if count == -1:
        count = len(uids)

    click.secho(
        'Starting generating {0} items, random {1} ...'.format(
            count, itemscount),
        fg='green')

    locations_pids = Location.get_all_pids()
    patrons_barcodes = get_patrons_barcodes()
    missing *= len(patrons_barcodes)
    members_pids = Member.get_all_pids()
    with click.progressbar(reversed(uids[:count]), length=count) as bar:
        for id in bar:
            document = DocumentsWithItems.get_record_by_id(id)
            if document.get('type') == 'ebook':
                continue
            for i in range(0, randint(1, itemscount)):
                missing, item = create_random_item(
                    locations_pids=locations_pids,
                    patrons_barcodes=patrons_barcodes,
                    members_pids=members_pids,
                    missing=missing,
                    verbose=False
                )
                document.add_item(item, dbcommit=True)
            document.dbcommit(reindex=reindex)
            RecordIndexer().client.indices.flush()


def create_random_item(locations_pids, patrons_barcodes, members_pids,
                       missing, verbose=False):
    """Create items with randomised values."""
    item_types = ['standard_loan', 'short_loan', 'on_site_consultation']
    data = {
        '$schema': 'https://ils.test.rero.ch/schema/items/item-v0.0.1.json',
        'barcode': '????',
        'call_number': '????',
        'location_pid': random.choice(locations_pids),
        'item_type': random.choice(item_types)
    }
    item = Item.create(data)

    n = int(item.pid)
    data['barcode'] = str(10000000000 + n)
    data['call_number'] = str(n).zfill(5)
    item.update(data)

    if randint(0, 5) == 0 and missing > 0:
        item.lose_item()
        missing -= 1
    if verbose:
        click.echo(item.id)
    item.update(data)
    return missing, item


def get_patrons_barcodes():
    """Get all barcodes of patrons."""
    ids = Patron.get_all_ids()
    barcodes = []
    for id in ids:
        patron = Patron.get_record_by_id(id)
        barcode = patron.get('barcode')
        if barcode:
            barcodes.append(barcode)
    return barcodes


def create_loan(patron_barcode, member_pid, short):
    """Create data dictionary for loan and request of item."""
    n = randint(0, 60)
    current_date = datetime.date.today()
    start_date = (current_date + datetime.timedelta(days=-n)).isoformat()
    if short:
        end = 30-n
    else:
        end = 45-n
    end_date = (current_date + datetime.timedelta(days=end)).isoformat()
    request = {
        'patron_barcode': patron_barcode,
        'pickup_member_pid': member_pid,
        'start_date': start_date,
        'end_date': end_date
    }
    return request


def create_request(patron_barcode, member_pid, short):
    """Create data dictionary for loan and request of item."""
    request_datetime = pytz.utc.localize(datetime.datetime.now()).isoformat()
    request = {
        'patron_barcode': patron_barcode,
        'pickup_member_pid': member_pid,
        'request_datetime': request_datetime
    }
    return request
