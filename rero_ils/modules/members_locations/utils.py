# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
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

"""Utilities functions for rero-ils."""

from flask import url_for
from invenio_indexer.api import RecordIndexer

from ..locations.api import Location
from ..members_locations.api import MemberWithLocations
from ..utils import clean_dict_keys


def delete_location(record_type, record_class, pid):
    """Save a record into the db and index it.

    If the location does not exists, it well be created
    and attached to the parent member.
    """
    location = record_class.get_record_by_pid(pid)
    member = MemberWithLocations.get_member_by_locationid(location.id)
    location.delete(delindex=False)
    member.remove_location(location, delindex=True)
    RecordIndexer().client.indices.flush()
    _next = url_for('invenio_records_ui.memb', pid_value=member.pid)
    return _next, location.pid


def save_location(data, record_type, record_class, parent_pid=None):
    """Save a record into the db and index it.

    If the item does not exists, it well be created
    and attached to the parent document.
    """
    pid = data.get('pid')
    data = clean_dict_keys(data)
    if pid:
        location = Location.get_record_by_pid(pid)
        location.update(data, dbcommit=False)
        member = MemberWithLocations.get_member_by_locationid(location.id)
    else:
        location = Location.create(data, dbcommit=False)
        member = MemberWithLocations.get_record_by_pid(parent_pid)
        member.add_location(location, dbcommit=False)
    member.dbcommit(reindex=True)
    RecordIndexer().client.indices.flush()
    _next = url_for('invenio_records_ui.memb', pid_value=member.pid)
    return _next, location.pid
