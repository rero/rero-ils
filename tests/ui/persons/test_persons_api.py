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

from rero_ils.modules.persons.api import Person, PersonsSearch, \
    person_id_fetcher


def test_person_create(app, person_data_tmp, caplog):
    """Test MEF person creation."""
    pers = Person.get_record_by_pid('1')
    assert not pers
    pers = Person.create(
        person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    assert pers == person_data_tmp
    assert pers.get('pid') == '1'

    pers = Person.get_record_by_pid('1')
    assert pers == person_data_tmp

    fetched_pid = person_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'pers'
    person_data_tmp['viaf_pid'] = '1234'
    pers = Person.create(
        person_data_tmp,
        dbcommit=True,
        delete_pid=True
    )
    pers = Person.get_record_by_pid('2')
    assert pers.get('viaf_pid') == '1234'

    assert pers.organisation_pids == []

    pers.delete_from_index()
    # test the messages from current_app.logger
    assert caplog.records[0].name == 'elasticsearch'
    assert caplog.record_tuples[1] == (
        'flask.app', 30, 'Can not delete from index Person: 2'
    )


@mock.patch('requests.get')
def test_person_mef_create(mock_persons_mef_get, app, person_data_tmp,
                           person_response_data):
    """Test MEF person creation."""
    count = Person.count()
    mock_persons_mef_get.return_value = mock_response(
        json_data=person_response_data
    )
    pers_mef, online = Person.get_record_by_ref(
        'https://mef.rero.ch/api/rero/A017671081')
    flush_index(PersonsSearch.Meta.index)
    assert pers_mef == person_data_tmp
    assert online
    assert Person.count() == count + 1
    pers_mef.pop('rero')
    pers_mef.pop('gnd')
    pers_mef['sources'] = ['bnf']
    pers_mef.replace(pers_mef, dbcommit=True)
    pers_db, online = Person.get_record_by_ref(
        'https://mef.rero.ch/api/gnd/172759757')
    assert pers_db['sources'] == ['bnf']
    assert not online
