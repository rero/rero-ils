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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Mef contributions Record tests."""

from utils import get_mapping

from rero_ils.modules.contributions.api import Contribution, \
    ContributionsSearch


def test_contribution_es_mapping(es_clear, db, contribution_person_data_tmp):
    """Test mef elasticsearch mapping."""
    search = ContributionsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Contribution.create(
        contribution_person_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_contributions_search_mapping(app, contribution_person):
    """Test Mef contributions search mapping."""
    search = ContributionsSearch()

    count = search.query(
        'query_string', query='philosophische Fakultät').count()
    assert count == 1

    count = search.query(
        'match',
        **{'gnd.preferred_name': 'Loy'}).\
        count()
    assert count == 1

    count = search.query(
        'match',
        **{'gnd.variant_name': 'Madeiros'}).\
        count()
    assert count == 1
