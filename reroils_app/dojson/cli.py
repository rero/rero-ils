# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line utilities."""

from __future__ import absolute_import, print_function

import click
from flask import current_app
from werkzeug.local import LocalProxy

from reroils_app.modules.documents_items.cli import create_items
from reroils_app.modules.organisations_members.cli import import_organisations

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


@click.group()
def fixtures():
    """Fixtures management commands."""


fixtures.add_command(import_organisations)
fixtures.add_command(create_items)


@click.command('reverse')
def reverse():
    """Reverse the order of the data."""
    def processor(iterator):
        items = []
        for item in iterator:
            items.append(item)
        items.reverse()
        return items

    return processor


@click.command('head')
@click.argument('max', type=click.INT,)
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
