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

"""Jinja2 filters tests."""

from rero_ils.filter import format_date_filter, jsondumps, text_to_id, \
    to_pretty_json


def test_date_filter_format_timestamp_en(app):
    """Test full english date and tile filter."""
    datestring = format_date_filter('2018-06-06T09:29:55.947149+00:00')
    assert 'Wednesday, June 6, 2018, 11:29:55 AM' in datestring

    datestring = format_date_filter(
        '2018-06-06T09:29:55.947149+00:00', locale='fr')
    assert 'mercredi 6 juin 2018, 11:29:55' in datestring

    datestring = format_date_filter(
        '1950-01-01', date_format='short', time_format=None, locale='fr_CH')
    assert '01.01' in datestring


def test_date_filter_format_default_en(app):
    """Test medium english date filter."""
    datestring = format_date_filter(
        '1950-01-01', date_format='short', time_format=None)
    assert '1/1/50' in datestring


def test_date_filter_timezone(app):
    """Test medium english date filter."""
    datestring = format_date_filter(
        '2018-06-06T09:29:55.947149+00:00', timezone='Europe/Helsinki')
    assert 'Wednesday, June 6, 2018, 12:29:55 PM' in datestring


def test_date_filter_format_medium_date_en(app):
    """Test medium_date english date filter."""
    datestring = format_date_filter(
        '1950-01-01', date_format='medium', time_format=None)
    assert 'Jan 1, 1950' in datestring


def test_date_filter_format_full_en(app):
    """Test full english date filter."""
    datestring = format_date_filter(
        '1950-01-01', date_format='full', time_format=None)
    assert 'Sunday, January 1, 1950' in datestring


def test_date_filter_format_full_fr(app):
    """Test full french date filter."""
    datestring = format_date_filter(
        '1950-01-01', date_format='full', time_format=None, locale='fr')
    assert 'dimanche 1 janvier 1950' in datestring


def test_date_filter_format_short_fr(app):
    """Test short french date filter with pernicious date."""
    datestring = format_date_filter(
        '2006-08-14', date_format='short', time_format=None, locale='fr_CH')
    assert datestring == '14.08.06'


def test_time_filter_format_default(app):
    """Test default time."""
    datestring = format_date_filter(
         '2018-06-06T09:29:55.947149+00:00', date_format=None)
    assert datestring == '11:29:55 AM'


def test_time_filter_format_fr(app):
    """Test default time."""
    datestring = format_date_filter(
         '2018-06-06T09:29:55.947149+00:00', date_format=None, locale='fr')
    assert datestring == '11:29:55'


def test_time_filter_format_delimiter(app):
    """Test default time."""
    datestring = format_date_filter(
         '2018-06-06T09:29:55.947149+00:00', delimiter=' - ')
    assert datestring == 'Wednesday, June 6, 2018 - 11:29:55 AM'


def test_to_pretty():
    """Test json prettx."""
    data = {'test': '1'}
    new_data = '{\n    "test": "1"\n}'
    assert to_pretty_json(data) == new_data
    assert jsondumps(data) == new_data


def test_text_to_id():
    """Test text to id."""
    assert 'LoremIpsum' == text_to_id('Lorem Ipsum')
