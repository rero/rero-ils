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

"""Item filters tests."""

from rero_ils.modules.items.views import format_item_call_number


def test_items_call_number_filter(app):
    """Test call number format."""
    item = {'call_number': '00123'}
    results = '00123'
    assert results == format_item_call_number(item)

    item = {'call_number': '00123', 'second_call_number': '00456'}
    results = '00123 | 00456'
    assert results == format_item_call_number(item)
