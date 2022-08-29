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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

import mock
from utils import flush_index, mock_response

from rero_ils.modules.contributions.api import Contribution, \
    ContributionsSearch, contribution_id_fetcher


def test_contribution_create(app, contribution_person_data_tmp, caplog):
    """Test MEF contribution creation."""
    pers = Contribution.get_record_by_pid('1')
    assert not pers
    pers = Contribution.create(
        contribution_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    assert pers == contribution_person_data_tmp
    assert pers.get('pid') == '1'

    pers = Contribution.get_record_by_pid('1')
    assert pers == contribution_person_data_tmp

    fetched_pid = contribution_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'cont'
    contribution_person_data_tmp['viaf_pid'] = '1234'
    pers = Contribution.create(
        contribution_person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    pers = Contribution.get_record_by_pid('2')
    assert pers.get('viaf_pid') == '1234'

    assert pers.organisation_pids == []

    pers.delete_from_index()
    # test the messages from current_app.logger
    assert caplog.records[0].name == 'elasticsearch'
    assert caplog.record_tuples[1] == (
        'invenio', 30, 'Can not delete from index Contribution: 2'
    )


@mock.patch('requests.get')
def test_contribution_mef_create(mock_contributions_mef_get, app,
                                 contribution_person_data_tmp,
                                 contribution_person_response_data):
    """Test MEF contribution creation."""
    count = Contribution.count()
    mock_contributions_mef_get.return_value = mock_response(
        json_data=contribution_person_response_data
    )
    pers_mef, source, online = Contribution.get_record_by_ref(
        'https://mef.rero.ch/api/agents/rero/A017671081')
    flush_index(ContributionsSearch.Meta.index)
    assert pers_mef == contribution_person_data_tmp
    assert source == 'rero'
    assert online
    assert Contribution.count() == count + 1
    pers_mef.pop('idref')
    pers_mef['sources'] = ['gnd']
    pers_mef.replace(pers_mef, dbcommit=True)
    pers_db, source, online = Contribution.get_record_by_ref(
        'https://mef.rero.ch/api/agents/gnd/13343771X')
    assert pers_db['sources'] == ['gnd']
    assert source == 'gnd'
    assert not online
