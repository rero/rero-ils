# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Tests ui for collections."""


from rero_ils.modules.collections.api import Collection
from rero_ils.modules.collections.views import _start_end_date, get_teachers


def test_get_teachers(db, coll_martigny_1_data):
    """Test get teachers."""
    result = 'Pr. Smith, John, Pr. Nonyme, Anne'
    assert get_teachers(coll_martigny_1_data) == result


def test_start_end_date(db, coll_martigny_1_data):
    """Test date format."""
    result = '01/09/2020 - 31/12/2020'
    coll = Collection.create(coll_martigny_1_data, delete_pid=True)
    assert _start_end_date(
        coll.get('start_date'),
        coll.get('end_date')
    ) == result
