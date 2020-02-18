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

"""Test utils."""

from rero_ils.modules.documents.api import Document
from rero_ils.modules.utils import get_ref_for_pid


def test_get_ref_for_pid(app):
    """Test get $ref for pid."""
    url = 'https://ils.rero.ch/api/documents/3'
    assert get_ref_for_pid('documents', '3') == url
    assert get_ref_for_pid('doc', '3') == url
    assert get_ref_for_pid(Document, '3') == url
    assert get_ref_for_pid('test', '3') is None
