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

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import datetime
import json
import random
import string
from random import randint

import click
from flask.cli import with_appcontext

from .models import ItemIdentifier, ItemNoteTypes, ItemStatus
from ..documents.api import Document
from ..holdings.models import HoldingIdentifier
from ..item_types.api import ItemType
from ..items.api import Item
from ..locations.api import Location
from ..patrons.api import Patron
from ..utils import get_base_url


class StreamArray(list):
    """Converts a generator into a list to be json serialisable."""

    def __init__(self, generator):
        """Streamarray init."""
        self.generator = generator
        self._len = 1

    def __iter__(self):
        """Iterator."""
        self._len = 0
        for item in self.generator:
            yield item
            self._len += 1

    def __len__(self):
        """Record length."""
        return self._len


@click.command('reindex_items')
@with_appcontext
def reindex_items():
    """Reindexing of item."""
    with click.progressbar(ids, length=Item.count()) as bar:
        for uuid in bar:
            item = Item.get_record_by_id(uuid)
            item.reindex()


@click.command('create_items')
@click.option('-c', '--count', 'count',
              type=click.INT, default=-1, help='default=for all records')
@click.option('-i', '--itemscount', 'itemscount',
              type=click.INT, default=1, help='default=1')
@click.option('-m', '--missing', 'missing',
              type=click.INT, default=5, help='default=5')
# @click.argument('output', type=click.File('w'))
@click.option('-t', '--items_f', 'items_f', help='Items output file.')
@click.option('-h', '--holdings_f', 'holdings_f', help='Holdings output file.')
@with_appcontext
def create_items(count, itemscount, missing, items_f, holdings_f):
    """Create circulation items."""
    def generate(count, itemscount, missing):

        if count == -1:
            count = Document.count()

        click.secho(
            'Starting generating {count} items, random {itemsc} ...'.format(
                count=count,
                itemsc=itemscount
            ),
            fg='green',
        )

        locations_pids = get_locations()
        item_types_pids = get_item_types()
        patrons_barcodes = get_patrons_barcodes()
        missing *= len(patrons_barcodes)
        item_pid = ItemIdentifier.max() + 1
        holding_pid = HoldingIdentifier.max()
        status = None

        workshop_item = 1
        documents_pids = Document.get_all_pids()
        with click.progressbar(
                reversed(list(documents_pids)[:count]), length=count) as bar:
            for document_pid in bar:
                holdings = [{}]
                # we will not create holdings for ebook and journal documents
                if Document.get_record_by_pid(
                        document_pid).get('type') in ['ebook', 'journal']:
                    continue
                for i in range(0, randint(1, itemscount)):
                    org = random.choice(list(locations_pids.keys()))
                    location_pid = random.choice(locations_pids[org])
                    item_type_pid = random.choice(item_types_pids[org])
                    new_acquisition = bool(random.getrandbits(1))
                    holding_found = False
                    new_holding = None
                    for hold in holdings:
                        if hold.get('location_pid') == location_pid and \
                                hold.get('item_type_pid') == item_type_pid:
                            item_holding_pid = hold.get('pid')
                            holding_found = True
                    if not holding_found:
                        holding_pid += 1
                        item_holding_pid = holding_pid
                        holdings.append(
                            {'pid': item_holding_pid,
                             'location_pid': location_pid,
                             'item_type_pid': item_type_pid})
                        new_holding = create_holding_record(
                            item_holding_pid, location_pid,
                            item_type_pid, document_pid)
                    if org == '3':
                        # set a prefix for items of the workshop organisation
                        barcode = 'fictive{0}'.format(workshop_item)
                        if workshop_item < 17:
                            # fix the status of the first 16 items to ON_SHELF
                            status = ItemStatus.ON_SHELF
                        workshop_item += 1

                    else:
                        barcode = str(10000000000 + item_pid)
                    missing, item = create_random_item(
                        item_pid=item_pid,
                        location_pid=location_pid,
                        missing=missing,
                        item_type_pid=item_type_pid,
                        document_pid=document_pid,
                        holding_pid=item_holding_pid,
                        barcode=barcode,
                        status=status,
                        new_acquisition=new_acquisition
                    )
                    item_pid += 1
                    yield item, new_holding

    items = []
    holdings = []
    with open(holdings_f, 'w', encoding='utf-8') as holdings_file:
        with open(items_f, 'w', encoding='utf-8') as items_file:
            for item, holding in generate(count, itemscount, missing):
                items.append(item)
                if holding:
                    holdings.append(holding)
            json.dump(items, indent=2, fp=items_file)
            json.dump(holdings, indent=2, fp=holdings_file)


def create_holding_record(
        holding_pid, location_pid, item_type_pid, document_pid):
    """Create items with randomised values."""
    base_url = get_base_url()
    url_api = '{base_url}/api/{doc_type}/{pid}'
    holding = {
        'pid': str(holding_pid),
        'location': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='locations', pid=location_pid)
        },
        'holdings_type': 'standard',
        'circulation_category': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='item_types', pid=item_type_pid)
        },
        'document': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='documents', pid=document_pid)
        }
    }
    return holding


def get_locations():
    """Get all locations.

    :return: A dict of list of pids with an organisation pid as key.
    """
    to_return = {}
    for pid in Location.get_all_pids():
        record = Location.get_record_by_pid(pid)
        if not record.get('is_online'):
            org_pid = record.get_library()\
                            .replace_refs().get('organisation').get('pid')
            to_return.setdefault(org_pid, []).append(pid)
    return to_return


def get_item_types():
    """Get all item types.

    :return: A dict of list of pids with an organisation pid as key.
    """
    to_return = {}
    for pid in ItemType.get_all_pids():
        record = ItemType.get_record_by_pid(pid).replace_refs()
        if record.get('type') != 'online':
            org_pid = record['organisation']['pid']
            to_return.setdefault(org_pid, []).append(pid)
    return to_return


def create_random_item(item_pid, location_pid, missing, item_type_pid,
                       document_pid, holding_pid, barcode, status,
                       new_acquisition):
    """Create items with randomised values."""
    if not status:
        status = ItemStatus.ON_SHELF
        if randint(0, 50) == 0 and missing > 0:
            status = ItemStatus.MISSING
            missing -= 1
    base_url = get_base_url()
    url_api = '{base_url}/api/{doc_type}/{pid}'
    item = {
        # '$schema': 'https://ils.rero.ch/schemas/items/item-v0.0.1.json',
        'pid': str(item_pid),
        'barcode': barcode,
        'call_number': str(item_pid).zfill(5),
        'status': status,
        'location': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='locations', pid=location_pid)
        },
        'item_type': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='item_types', pid=item_type_pid)
        },
        'document': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='documents', pid=document_pid)
        },
        'holding': {
            '$ref': url_api.format(
                base_url=base_url, doc_type='holdings', pid=holding_pid)
        },
        'type': 'standard'
    }
    # ACQUISITION DATE
    #   add acquisition date if item is a new acquisition
    #   choose a days delta between 1 past year to 1 month later than sysdate.
    if new_acquisition:
        diff = datetime.timedelta(random.randint(-31, 365))
        acquisition_date = datetime.date.today() - diff
        item['acquisition_date'] = acquisition_date.strftime('%Y-%m-%d')

    # RANDOMLY ADD NOTES
    #   we will add a note to +/- 60% of the items.
    #   if an item has notes, between one and 9 notes will be add
    if random.random() < 0.6:
        item['notes'] = random.sample([{
            'type': ItemNoteTypes.GENERAL,
            'content': 'Here you can read a general/public note'
        }, {
            'type': ItemNoteTypes.STAFF,
            'content': 'This is a staff note only visible by staff members.'
        }, {
            'type': ItemNoteTypes.CHECKIN,
            'content': 'Checkin note for {0}'.format(barcode)
        }, {
            'type': ItemNoteTypes.CHECKOUT,
            'content': 'Checkout note for {0}'.format(barcode)
        }, {
            'type': ItemNoteTypes.ACQUISITION,
            'content': 'Acquisition note content'
        }, {
            'type': ItemNoteTypes.BINDING,
            'content': 'Link with an other item (same subject) : '
                       '<a href="javascript:void()">dummy_link</a>'
        }, {
            'type': ItemNoteTypes.PROVENANCE,
            'content': 'Antique library collection'
        }, {
            'type': ItemNoteTypes.CONDITION,
            'content': 'Missing some pages :-('
        }, {
            'type': ItemNoteTypes.PATRIMONIAL,
            'content': 'Part of the UNESCO books collection'
        }], k=random.randint(1, 9))

    # RANDOMLY ADD SECOND CALL NUMBER
    #   we will add a second call number to +/- 25% of the items.
    if random.random() < 0.25:
        item['second_call_number'] = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )

    return missing, item


def get_patrons_barcodes():
    """Get all barcodes of patrons."""
    patrons_ids = Patron.get_all_ids()
    barcodes = []
    for uuid in patrons_ids:
        patron = Patron.get_record_by_id(uuid)
        barcode = patron.patron.get('barcode')
        if barcode:
            barcodes.append(barcode)
    return barcodes
