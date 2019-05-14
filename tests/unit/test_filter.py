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

from rero_ils.filter import format_date_filter, jsondumps, to_pretty_json


def test_date_filter_format_timestamp_en():
    """Test timestamp english date filter."""
    datestring = format_date_filter('2018-06-06T09:29:55.947149+00:00',
                                    'timestamp')
    assert '06.06.2018 09:29' in datestring

    datestring = format_date_filter('1950-01-01', 'day_month', 'fr')
    assert '01.01' in datestring


def test_to_pretty():
    """Test json prettx."""
    data = {'test': '1'}
    new_data = '{\n    "test": "1"\n}'
    assert to_pretty_json(data) == new_data
    assert jsondumps(data) == new_data


def test_date_filter_format_default_en():
    """Test medium english date filter."""
    datestring = format_date_filter('1950-01-01')
    assert 'Sun 01.01.1950' in datestring


def test_date_filter_format_medium_date_en():
    """Test medium_date english date filter."""
    datestring = format_date_filter('1950-01-01', 'medium_date')
    assert '01 January 1950' in datestring


def test_date_filter_format_full_en():
    """Test full english date filter."""
    datestring = format_date_filter('1950-01-01', 'full')
    assert 'Sunday, 1. January 1950' in datestring


def test_date_filter_format_full_fr():
    """Test full french date filter."""
    datestring = format_date_filter('1950-01-01', 'full', 'fr')
    assert 'dimanche, 1. janvier 1950' in datestring
