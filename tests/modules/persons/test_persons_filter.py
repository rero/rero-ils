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

"""Jinja2 filters tests."""

from rero_ils.modules.persons.views import person_label, \
    person_merge_data_values


def test_person_merge_data_values(app, person_data, person_data_result):
    """Test persons merge data."""
    app.config['RERO_ILS_PERSONS_SOURCES'] = ['bnf', 'gnd', 'rero']
    data = person_merge_data_values(person_data)
    assert data == person_data_result


def test_person_label(app, person_data):
    """Test persons merge data."""
    app.config['RERO_ILS_PERSONS_LABEL_ORDER'] = {
        'fallback': 'fr',
        'fr': ['rero', 'bnf', 'gnd'],
        'de': ['gnd', 'rero', 'bnf']
    }
    label = person_label(person_data, 'fr')
    assert label == 'Cavalieri, Giovanni Battista'
    label = person_label(person_data, 'it')
    assert label == 'Cavalieri, Giovanni Battista'
