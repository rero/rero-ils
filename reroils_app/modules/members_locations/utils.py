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

from flask import url_for

from ..locations.api import Location
from ..members_locations.api import MemberWithLocations
from ..organisations_members.api import OrganisationWithMembers


def delete_location(record_type, pid, record_indexer, parent_pid):
    """Save a record into the db and index it.

    If the location does not exists, it well be created
    and attached to the parent member.
    """
    location = Location.get_record_by_pid(pid)
    persistent_identifier = location.persistent_identifier
    member = MemberWithLocations.get_record_by_pid(parent_pid)
    organisation = OrganisationWithMembers.get_organisation_by_memberid(
        member.id
    )
    member.remove_location(location, delindex=True)
    organisation.reindex()

    _next = url_for('invenio_records_ui.memb', pid_value=parent_pid)
    return _next, persistent_identifier


def save_location(data, record_type, fetcher, minter,
                  record_indexer, record_class, parent_pid):
    """Save a record into the db and index it.

    If the item does not exists, it well be created
    and attached to the parent document.
    """
    member = MemberWithLocations.get_record_by_pid(parent_pid)
    pid = data.get('pid')
    if pid:
        location = Location.get_record_by_pid(pid)
        location.update(data, dbcommit=True, reindex=True)
    else:
        location = Location.create(data, dbcommit=True, reindex=True)
        member.add_location(location, dbcommit=True, reindex=True)
    organisation = OrganisationWithMembers.get_organisation_by_memberid(
        member.id
    )
    organisation.reindex()

    _next = url_for('invenio_records_ui.memb', pid_value=parent_pid)
    return _next, location.persistent_identifier
