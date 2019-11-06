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

from rero_ils.modules.mef_persons.api import MefPerson
from rero_ils.modules.mef_persons.receivers import \
    publish_api_harvested_records


def test_mef_publish_api_harvested_records(app, mef_person_data_tmp, capsys):
    """Test mef person publish api harvested records."""
    publish_api_harvested_records(sender='test', name='mef',
                                  records=[mef_person_data_tmp],
                                  url='http://test.com')
    out, err = capsys.readouterr()
    assert out.strip() == (
        'mef harvester: received 1 records: '
        'https://ils.rero.ch/schema/persons/mef_person-v0.0.1.json'
    )
    assert len(list(MefPerson.get_all_pids())) == 1
