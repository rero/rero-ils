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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.patron_types.api import PatronType, PatronTypesSearch, \
    patron_type_id_fetcher


def test_patron_type_create(db, patron_type_data_tmp):
    """Test pttyanisation creation."""
    ptty = PatronType.create(patron_type_data_tmp, delete_pid=True)
    assert ptty == patron_type_data_tmp
    assert ptty.get('pid') == '1'

    ptty = PatronType.get_record_by_pid('1')
    assert ptty == patron_type_data_tmp

    fetched_pid = patron_type_id_fetcher(ptty.id, ptty)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'ptty'


def test_patron_type_es_mapping(es_clear, db, organisation,
                                patron_type_data_tmp):
    """."""
    search = PatronTypesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    PatronType.create(
        patron_type_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_patron_type_exist_name_and_organisation_pid(patron_type):
    """."""
    ptty = patron_type.replace_refs()
    assert PatronType.exist_name_and_organisation_pid(
        ptty.get('name'), ptty.get('organisation', {}).get('pid'))
    assert not PatronType.exist_name_and_organisation_pid(
        'not exists yet', ptty.get('organisation', {}).get('pid'))
