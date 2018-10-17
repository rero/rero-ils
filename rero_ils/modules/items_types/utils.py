# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2018 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Utilities functions for patrons_types."""


from __future__ import absolute_import, print_function

from flask import url_for
from invenio_indexer.api import RecordIndexer

from ..patrons.api import current_patron
from ..utils import clean_dict_keys


def save_item_type(data, record_type, record_class, parent_pid):
    """Save a record into the db and index it.

    If the patron_type does not exists, it well be created
    and attached to the organisation.
    """
    data = clean_dict_keys(data)
    pid = data.get('pid')
    if pid:
        item_type = record_class.get_record_by_pid(pid)
        item_type.update(data, dbcommit=True, reindex=True)
    else:
        data['organisation_pid'] = current_patron.organisation.pid
        item_type = record_class.create(data, dbcommit=True, reindex=True)
    RecordIndexer().client.indices.flush()

    _next = url_for('invenio_records_ui.ptty', pid_value=item_type.pid)
    return _next, item_type.pid
