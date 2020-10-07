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

from rero_ils.modules.contributions.api import Contribution
from rero_ils.modules.contributions.tasks import create_mef_records, \
    delete_records


def test_contribution_create_delete(app, contribution_person_data_tmp, capsys):
    """Test mef contributions creation and deletion."""
    count = create_mef_records([contribution_person_data_tmp], verbose=True)
    assert count == 1
    out, err = capsys.readouterr()
    pers = Contribution.get_record_by_pid('cont_pers')
    assert out.strip() == 'record uuid: {id}'.format(id=pers.id)
    count = delete_records([pers], verbose=True)
    assert count == 1
    out, err = capsys.readouterr()
    assert out.strip() == 'records deleted: 1'
