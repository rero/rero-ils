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

"""Babel extractors tests."""

from rero_ils.modules.babel_extractors import extract_json


def test_babel_extractors_extract_json(babel_filehandle):
    """Test extract json."""
    translations = extract_json(
        fileobj=babel_filehandle,
        keywords=None,
        comment_tags=None,
        options={"keys_to_translate": "['title']"},
    )
    assert translations == [
        (4, "gettext", "Organisation", []),
        (14, "gettext", "Schema", []),
        (21, "gettext", "Organisation ID", []),
        (25, "gettext", "Name", []),
    ]
