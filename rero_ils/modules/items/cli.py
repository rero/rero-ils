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

import json
import random
from random import randint

import click
from flask.cli import with_appcontext

from .models import ItemIdentifier, ItemStatus
from ..documents.api import Document
from ..item_types.api import ItemType
from ..items.api import Item
from ..locations.api import Location
from ..patrons.api import Patron


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
    ids = Item.get_all_ids()
    with click.progressbar(ids, length=len(ids)) as bar:
        for uuid in bar:
            item = Item.get_record_by_id(uuid)
            item.reindex()


@click.command('create_items')
@click.option(
    '-c', '--count', 'count',
    type=click.INT, default=-1, help='default=for all records'
)
@click.option(
    '-i', '--itemscount', 'itemscount',
    type=click.INT, default=1, help='default=1'
)
@click.option(
    '-m', '--missing', 'missing', type=click.INT, default=5, help='default=5'
)
@click.argument('output', type=click.File('w'))
@with_appcontext
def create_items(output, count, itemscount, missing):
    """Create circulation items."""
    def generate(count, itemscount, missing):

        documents_pids = Document.get_all_pids()

        if count == -1:
            count = len(documents_pids)

        click.secho(
            'Starting generating {0} items, random {1} ...'.format(
                count, itemscount),
            fg='green',
        )

        locations_pids = get_locations()
        item_types_pids = get_item_types()
        patrons_barcodes = get_patrons_barcodes()
        missing *= len(patrons_barcodes)
        item_pid = ItemIdentifier.max() + 1
        with click.progressbar(
                reversed(documents_pids[:count]), length=count) as bar:
            for document_pid in bar:
                if Document.get_record_by_pid(
                        document_pid).get('type') == 'ebook':
                    continue
                for i in range(0, randint(1, itemscount)):
                    missing, item = create_random_item(
                        item_pid=item_pid,
                        locations_pids=locations_pids,
                        patrons_barcodes=patrons_barcodes,
                        missing=missing,
                        item_types_pids=item_types_pids,
                        document_pid=document_pid
                    )
                    item_pid += 1
                    yield item
    for chunk in json.JSONEncoder(indent=2)\
            .iterencode(StreamArray(generate(count, itemscount, missing))):
        output.write(chunk)


def get_locations():
    """Get all locations.

    :returns: A dict of list of pids with an organisation pid as key.
    """
    to_return = {}
    for pid in Location.get_all_pids():
        org_pid = Location.get_record_by_pid(pid).get_library()\
                          .replace_refs().get('organisation').get('pid')
        to_return.setdefault(org_pid, []).append(pid)
    return to_return


def get_item_types():
    """Get all item types.

    :returns: A dict of list of pids with an organisation pid as key.
    """
    to_return = {}
    for pid in ItemType.get_all_pids():
        org_pid = ItemType.get_record_by_pid(pid)\
            .replace_refs()['organisation']['pid']
        to_return.setdefault(org_pid, []).append(pid)
    return to_return


def create_random_item(
    item_pid,
    locations_pids,
    patrons_barcodes,
    missing,
    item_types_pids,
    document_pid
):
    """Create items with randomised values."""
    status = ItemStatus.ON_SHELF
    if randint(0, 5) == 0 and missing > 0:
        status = ItemStatus.MISSING
        missing -= 1
    url_api = 'https://ils.rero.ch/api/{doc_type}/{pid}'
    org = random.choice(list(locations_pids.keys()))
    item = {
        # '$schema': 'https://ils.rero.ch/schema/items/item-v0.0.1.json',
        'barcode': str(10000000000 + item_pid),
        'call_number': str(item_pid).zfill(5),
        'status': status,
        'location': {
            '$ref': url_api.format(
                doc_type='locations', pid=random.choice(locations_pids[org]))
        },
        'item_type': {
            '$ref': url_api.format(
                doc_type='item_types', pid=random.choice(item_types_pids[org]))
        },
        'document': {
            '$ref': url_api.format(
                doc_type='documents', pid=document_pid)
        }
    }
    return missing, item


def get_patrons_barcodes():
    """Get all barcodes of patrons."""
    patrons_ids = Patron.get_all_ids()
    barcodes = []
    for uuid in patrons_ids:
        patron = Patron.get_record_by_id(uuid)
        barcode = patron.get('barcode')
        if barcode:
            barcodes.append(barcode)
    return barcodes
