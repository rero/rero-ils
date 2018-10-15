# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Views tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import url_for

from rero_ils.views import nl2br


@pytest.mark.skip(reason="will erase ES index")
def test_ping(client):
    """Test the ping view."""
    resp = client.get(url_for('rero_ils.ping'))
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == 'OK'


def test_nl2br():
    """Test nl2br function view."""
    assert 'foo<br>Bar' == nl2br('foo\nBar')
