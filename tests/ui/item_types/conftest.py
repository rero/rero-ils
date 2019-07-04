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

"""Common pytest item_types."""

import pytest

from invenio_search import current_search, current_search_client


@pytest.yield_fixture(scope='module')
def item_types_records(
    item_type_standard_martigny,
    item_type_on_site_martigny,
    item_type_specific_martigny,
    item_type_regular_sion
):
    """Item types for test mapping."""
    pass
