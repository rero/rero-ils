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

"""Mef Persons Record tests."""

from utils import get_mapping

from rero_ils.modules.mef_persons.api import MefPerson, MefPersonsSearch


def test_mef_persons_search_mapping(
    app, mef_person
):
    """Test Mef Persons search mapping."""
    search = MefPersonsSearch()

    c = search.query('query_string', query='ordonné prêtre').count()
    assert c == 1

    c = search.query('query_string', query='ordonne pretre').count()
    assert c == 1

    c = search.query(
        'match',
        **{'bnf.biographical_information': 'ordonné'}).\
        count()
    assert c == 1

    c = search.query(
        'match',
        **{'bnf.biographical_information': 'ordonne'}).\
        count()
    assert c == 1

    c = search.query(
        'match',
        **{'gnd.preferred_name_for_person': 'Arnoudt'}).\
        count()
    assert c == 1

    c = search.query(
        'match',
        **{'gnd.variant_name_for_person': 'Arnoudt'}).\
        count()
    assert c == 1


def test_mef_person_es_mapping(es_clear, db, mef_person_data_tmp):
    """Test mef elasticsearch mapping."""
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
