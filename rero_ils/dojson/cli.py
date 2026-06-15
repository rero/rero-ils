# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Click command-line utilities."""

import json

import click
from flask import current_app
from werkzeug.local import LocalProxy

_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


@click.command("reverse")
def reverse():
    """Reverse the order of the data."""

    def processor(iterator):
        items = []
        for item in iterator:
            items.append(item)
        items.reverse()
        return items

    return processor


@click.command("head")
@click.argument(
    "max",
    type=click.INT,
)
def head(max):
    """Take only the first max items."""

    def processor(iterator):
        n = 0
        for item in iterator:
            if n >= max:
                raise StopIteration
            n += 1
            yield item

    return processor


def pretty_json_dump(iterator):
    """Dump JSON from iterator."""
    return json.dumps(list(iterator), indent=2)
