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

"""Organisation with Members module tests."""

from __future__ import absolute_import, print_function

import mock
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata

from reroils_app.modules.members.api import Member
from reroils_app.modules.members_locations.api import MemberWithLocations
from reroils_app.modules.organisations_members.api import \
    OrganisationWithMembers
from reroils_app.modules.organisations_members.models import \
    OrganisationsMembersMetadata


def test_organisation_members_create(db, minimal_organisation_record,
                                     minimal_member_record):
    """Test organisation with members creation."""
    org = OrganisationWithMembers.create(
        minimal_organisation_record,
        dbcommit=True
    )
    memb = MemberWithLocations.create(minimal_member_record, dbcommit=True)
    assert org.members == []

    org.add_member(memb, dbcommit=True)
    assert org.members[0] == memb

    dump = org.dumps()
    assert dump['members'][0] == memb.dumps()


@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
def test_delete_member(reindex, db,
                       minimal_organisation_record,
                       minimal_member_record):
    """Test OrganisationsMembers delete."""
    org = OrganisationWithMembers.create(
        minimal_organisation_record,
        dbcommit=True
    )
    member = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    org.add_member(member, dbcommit=True)
    pid = PersistentIdentifier.get_by_object('memb', 'rec', member.id)
    assert pid.is_registered()
    org.remove_member(member)
    assert pid.is_deleted()
    assert org.members == []

    member1 = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    org.add_member(member1, dbcommit=True)
    member2 = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    org.add_member(member2, dbcommit=True)
    member3 = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    org.add_member(member3, dbcommit=True)
    org.remove_member(member2)
    assert len(org.members) == 2
    assert org.members[0]['pid'] == '2'
    assert org.members[1]['pid'] == '4'


@mock.patch('reroils_app.modules.api.IlsRecord.reindex')
def test_delete_organisation(reindex, db,
                             minimal_organisation_record,
                             minimal_member_record):
    """Test Organisation delete."""
    org = OrganisationWithMembers.create(
        minimal_organisation_record,
        dbcommit=True
    )
    member1 = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    pid1 = PersistentIdentifier.get_by_object('memb', 'rec', member1.id)
    member2 = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    pid2 = PersistentIdentifier.get_by_object('memb', 'rec', member2.id)
    member3 = MemberWithLocations.create(
        minimal_member_record,
        dbcommit=True
    )
    pid3 = PersistentIdentifier.get_by_object('memb', 'rec', member3.id)
    org.add_member(member1, dbcommit=True)
    org.add_member(member2, dbcommit=True)
    org.add_member(member3, dbcommit=True)
    assert OrganisationsMembersMetadata.query.count() == 3
    assert RecordMetadata.query.count() == 4
    assert pid1.is_registered()
    assert pid2.is_registered()
    assert pid3.is_registered()
    org.delete(force=True)
    assert OrganisationsMembersMetadata.query.count() == 0
    assert RecordMetadata.query.count() == 0
    assert pid1.is_deleted()
    assert pid2.is_deleted()
    assert pid3.is_deleted()
