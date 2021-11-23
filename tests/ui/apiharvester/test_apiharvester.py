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

"""Api harvester tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import mock
import pytest
from utils import mock_response

from rero_ils.modules.apiharvester.api import ApiHarvester
from rero_ils.modules.apiharvester.tasks import harvest_records
from rero_ils.modules.contributions.api import Contribution, \
    ContributionsSearch


@mock.patch('requests.Session.get')
def test_api_harvester(mock_get, app, capsys, document,
                       contribution_person_data,
                       contribution_person_response_data):
    """Test api source creation update."""
    configs = ApiHarvester.get_all_configs()
    with pytest.raises(StopIteration):
        next(configs)
    configs = app.config.get('RERO_ILS_API_HARVESTER', {})
    for name, data in configs.items():
        db_config = ApiHarvester(name)
        db_config = ApiHarvester.create(name=name, url=data['url'],
                                        size=data['size'])
        assert db_config.name == name
        assert db_config.url == data['url']
        assert db_config.size == data['size']
        assert db_config.lastrun
        assert db_config.id

    assert ApiHarvester.get_config('agent_mef') == db_config
    assert ApiHarvester.count() == 1

    # no coresponding contribution
    api_harvester = ApiHarvester('agent_mef')
    mock_get.return_value = mock_response(
        json_data=contribution_person_response_data)
    count, process_count = api_harvester.get_records()
    assert count == 1
    assert process_count == {'agent_mef': 0}

    # coresponding contribution
    data = deepcopy(contribution_person_data)
    data.pop('gnd')
    Contribution.create(data=data, dbcommit=True, reindex=True)
    api_harvester = ApiHarvester('agent_mef')
    ContributionsSearch.flush_and_refresh()
    mock_get.return_value = mock_response(
        json_data=contribution_person_response_data)
    lastrun = api_harvester.lastrun
    from_date = lastrun.isoformat()
    from_date = from_date.replace(':', '%5C:')

    count, process_count = api_harvester.get_records(verbose=True)
    assert count == 1
    assert process_count == {'agent_mef': 1}
    out, err = capsys.readouterr()
    assert out.strip().split('\n') == [
        'API records found: 1',
        '1          URL: https://mef.rero.ch/api/mef'
        f'?size=1000&q=_updated:>{from_date}',
        '  Update contribution: cont_pers documents: 0'
    ]
    assert api_harvester.lastrun != lastrun

    mock_get.return_value = mock_response(
        json_data=contribution_person_response_data)
    count, process_count = harvest_records('agent_mef')
    assert count == 1
    assert process_count == {'agent_mef': 0}

    mock_get.return_value = mock_response(
        json_data=contribution_person_response_data)
    count, process_count = harvest_records('test')
    assert count == 0
    assert process_count == {}
