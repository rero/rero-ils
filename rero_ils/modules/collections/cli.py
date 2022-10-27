# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Click command-line interface for collection record management."""

from __future__ import absolute_import, print_function

import json
import random

import click
from flask.cli import with_appcontext

from rero_ils.modules.collections.api import Collection
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.utils import extracted_data_from_ref, get_ref_for_pid


@click.command('create_collections')
@click.option('-f', '--requests_file', 'input_file', help='Request input file')
@with_appcontext
def create_collections(input_file, max_item=10):
    """Create collections."""
    organisation_items = {}
    with open(input_file, 'r', encoding='utf-8') as request_file:
        collections = json.load(request_file)
        for collection_data in collections:
            organisation_pid = extracted_data_from_ref(
                collection_data.get('organisation').get('$ref'))
            if organisation_pid not in organisation_items:
                organisation_items[organisation_pid] =\
                    get_items_by_organisation_pid(organisation_pid)
            items = random.choices(
                organisation_items[organisation_pid],
                k=random.randint(1, max_item)
            )
            collection_data['items'] = []
            for item_pid in items:
                ref = get_ref_for_pid('items', item_pid)
                collection_data['items'].append({'$ref': ref})
            request = Collection.create(
                collection_data,
                dbcommit=True,
                reindex=True
            )
            click.echo(f'\tCollection: #{request.pid}')


def get_items_by_organisation_pid(organisation_pid):
    """Get items by organisation pid."""
    query = ItemsSearch().filter(
            'term', organisation__pid=organisation_pid)\
        .source('pid')
    return [item.pid for item in query.scan()]
