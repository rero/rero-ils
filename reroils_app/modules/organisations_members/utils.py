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
from flask_login import current_user

from ..members_locations.api import MemberWithLocations
from ..organisations_members.api import OrganisationWithMembers
from ..patrons.api import Patron


def delete_member(record_type, pid, record_indexer, parent_pid):
    """Remove an member from an organisation.

    If the location does not exists, it well be created
    and attached to the parent member.
    """
    member = MemberWithLocations.get_record_by_pid(pid)
    persistent_identifier = member.persistent_identifier
    organisation = OrganisationWithMembers.get_organisation_by_memberid(
        member.id
    )
    organisation.remove_member(member, delindex=True)

    _next = url_for('reroils_record_editor.search_memb')
    return _next, persistent_identifier


def save_member(data, record_type, fetcher, minter,
                record_indexer, record_class, parent_pid):
    """Save a record into the db and index it.

    If the item does not exists, it well be created
    and attached to the parent document.
    """
    patron = Patron.get_patron_by_user(current_user)
    organisation = OrganisationWithMembers.get_record_by_pid(
        patron.organisation_pid
    )
    pid = data.get('pid')
    if pid:
        member = MemberWithLocations.get_record_by_pid(pid)
        member.update(data, dbcommit=True, reindex=True)
    else:
        member = MemberWithLocations.create(data, dbcommit=True, reindex=True)
        organisation.add_member(member)
    organisation.dbcommit(reindex=True)

    _next = url_for('invenio_records_ui.memb', pid_value=member.pid)
    return _next, member.persistent_identifier
