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

"""Utilities functions for rerpils-app."""


from __future__ import absolute_import, print_function

import datetime

from flask import request

from reroils_app.modules.items.api import Item

from ..documents_items.api import DocumentsWithItems


def commit_item(item):
    """commit_changes item and document."""
    if not isinstance(item, Item):
        raise TypeError
    item.commit()
    item.dbcommit(reindex=True, forceindex=True)
    document = DocumentsWithItems.get_document_by_itemid(item.id)
    document.reindex()


def item_from_web_request(data):
    """Get item from web request data."""
    data = request.get_json()
    pid = data.pop('pid')
    return Item.get_record_by_pid(pid)


def request_start_end_date():
    """Get item request expiration date."""
    current_date = datetime.date.today()
    start_date = current_date.isoformat()
    end_date = (current_date + datetime.timedelta(days=45)).isoformat()
    return start_date, end_date
