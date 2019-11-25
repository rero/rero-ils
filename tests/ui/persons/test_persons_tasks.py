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

from rero_ils.modules.persons.tasks import create_mef_records, \
    delete_records
from rero_ils.modules.persons.api import Person


def test_person_create_delete(app, person_data_tmp, capsys):
    """Test mef persons creation and deletion."""
    count = create_mef_records([person_data_tmp], verbose=True)
    assert count == 1
    out, err = capsys.readouterr()
    pers = Person.get_record_by_pid('pers1')
    assert out.strip() == 'record uuid: {id}'.format(id=pers.id)
    count = delete_records([pers], verbose=True)
    assert count == 1
    out, err = capsys.readouterr()
    assert out.strip() == 'records deleted: 1'
