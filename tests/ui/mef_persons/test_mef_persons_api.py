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

from rero_ils.modules.mef_persons.api import MefPerson, MefPersonsSearch, \
    mef_person_id_fetcher


def test_mef_person_create(db, mef_person_data_tmp):
    """Test persanisation creation."""
    pers = MefPerson.get_record_by_pid('1')
    assert not pers
    pers, msg = MefPerson.create_or_update(
        mef_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    assert pers == mef_person_data_tmp
    assert pers.get('pid') == '1'

    pers = MefPerson.get_record_by_pid('1')
    assert pers == mef_person_data_tmp

    fetched_pid = mef_person_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'pers'
    mef_person_data_tmp['viaf_pid'] = '1234'
    pers, msg = MefPerson.create_or_update(
        mef_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    pers = MefPerson.get_record_by_pid('1')
    assert pers.get('viaf_pid') == '1234'


def test_mef_person_es_mapping(es_clear, db, mef_person_data_tmp):
    """."""
    search = MefPersonsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    MefPerson.create(
        mef_person_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
