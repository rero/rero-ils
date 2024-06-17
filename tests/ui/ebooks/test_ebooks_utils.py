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

"""Test ebook utils."""

from rero_ils.modules.ebooks.utils import add_oai_source


def test_add_oai_source(app):
    """Test add oai source."""
    msg = add_oai_source(name="test", baseurl="http://test.com")
    assert msg == "Added"
    msg = add_oai_source(name="test", baseurl="http://test.com")
    assert msg == "Not Updated"
    msg = add_oai_source(
        name="test",
        baseurl="http://test.com",
        setspecs="specs",
        comment="comment",
        update=True,
    )
    assert msg == "Updated"
