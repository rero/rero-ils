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

"""Tests UI view for patrons."""


import mock
from flask import url_for
from utils import mock_response


@mock.patch('requests.get')
def test_mef_persons_detailed_view(mock_get, client, mef_person_data):
    """Test mef detailed view."""
    json_data = {'metadata': mef_person_data}
    mock_get.return_value = mock_response(json_data=json_data)
    # check redirection
    res = client.get(url_for(
        'mef_persons.persons_detailed_view', viewcode='global', pid='pers1'))
    assert res.status_code == 200

# TODO: add search view
