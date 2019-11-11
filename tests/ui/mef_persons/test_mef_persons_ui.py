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

"""Tests UI view for MEF persons."""


import mock
from flask import url_for
from rero_ils.modules.mef_persons.views import person_label


def test_mef_persons_detailed_view(client, mef_person):
    """Test mef detailed view."""
    # check detailed view global
    res = client.get(url_for(
        'mef_persons.persons_detailed_view', viewcode='global', pid='pers1'))
    assert res.status_code == 200


def test_mef_persons_filter_detailed_view(client,
                                          mef_person,
                                          loc_public_sion):
    """Test mef detailed view."""
    # check detailed view for organisation 2
    res = client.get(url_for(
        'mef_persons.persons_detailed_view', viewcode='org2', pid='pers1'))
    assert res.status_code == 200


def test_person_label(mef_person):
    """Test person_label function view."""
    assert 'Arnoudt, Pierre J.' == person_label(mef_person, 'fr')
    assert '-' == person_label({}, 'fr')


# TODO: add search view
