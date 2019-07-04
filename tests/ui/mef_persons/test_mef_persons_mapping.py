# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
