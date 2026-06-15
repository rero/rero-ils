# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line interface for collection record management."""

import json
import random

import click
from flask.cli import with_appcontext

from rero_ils.modules.collections.api import Collection
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.utils import extracted_data_from_ref, get_ref_for_pid


@click.command("create_collections")
@click.option("-f", "--requests_file", "input_file", help="Request input file")
@with_appcontext
def create_collections(input_file, max_item=10):
    """Create collections."""
    with open(input_file, encoding="utf-8") as request_file:
        collections = json.load(request_file)
        for collection_data in collections:
            libraries_pids = [
                extracted_data_from_ref(library.get("$ref")) for library in collection_data.get("libraries")
            ]
            eligible_items = get_items_by_libraries_pid(libraries_pids)
            items = random.choices(eligible_items, k=random.randint(1, max_item))
            collection_data["items"] = []
            for item_pid in items:
                ref = get_ref_for_pid("items", item_pid)
                collection_data["items"].append({"$ref": ref})
            request = Collection.create(collection_data, dbcommit=True, reindex=True)
            click.echo(f"\tCollection: #{request.pid}")


def get_items_by_libraries_pid(libraries_pids):
    """Get items by organisation pid."""
    query = ItemsSearch().filter("terms", library__pid=libraries_pids).source("pid")
    return [item.pid for item in query.scan()]
