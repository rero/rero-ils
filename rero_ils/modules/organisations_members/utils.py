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
from flask_login import current_user
from invenio_indexer.api import RecordIndexer

from ..patrons.api import Patron
from ..utils import clean_dict_keys
from .api import OrganisationWithMembers


def delete_member(record_type, record_class, pid):
    """Remove an member from an organisation.

    If the location does not exists, it well be created
    and attached to the parent member.
    """
    member = record_class.get_record_by_pid(pid)
    organisation = OrganisationWithMembers.get_organisation_by_memberid(
        member.id
    )
    member.delete(delindex=True)
    organisation.remove_member(member, delindex=False)
    RecordIndexer().client.indices.flush()
    _next = url_for('memb.index_view')
    return _next, member.pid


def save_member(data, record_type, record_class, parent_pid=None):
    """Save a record into the db and index it.

    If the item does not exists, it well be created
    and attached to the parent document.
    """
    pid = data.get('pid')
    data = clean_dict_keys(data)
    patron = Patron.get_patron_by_user(current_user)
    organisation = OrganisationWithMembers.get_record_by_pid(
        patron.organisation.pid
    )
    if pid:
        member = record_class.get_record_by_pid(pid)
        member.update(data, dbcommit=False, reindex=False)
    else:
        member = record_class.create(data, dbcommit=False, reindex=False)
        organisation.add_member(member)
    member.dbcommit(reindex=True)
    RecordIndexer().client.indices.flush()
    _next = url_for('invenio_records_ui.memb', pid_value=member.pid)
    return _next, member.pid
