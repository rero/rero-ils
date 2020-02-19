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


"""Holding Patterns Record tests."""


from __future__ import absolute_import, print_function


def test_patterns_quarterly_one_level(
        db, es_clear, holding_lib_martigny_w_patterns,
        holding_lib_martigny):
    """Test holdings patterns annual two levels."""
    holding = holding_lib_martigny_w_patterns
    # test no prediction for monograph holdings record
    assert not holding_lib_martigny.increment_next_prediction()
    assert not holding_lib_martigny.next_issue_display_text
    assert not holding_lib_martigny.prediction_issues_preview(1)

    # test first issue
    assert holding.next_issue_display_text == 'no 61 2020 mars'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'no 62 2020 juin'
    for r in range(11):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'no 73 2023 mars'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'no 85 2026 mars'


def test_patterns_yearly_one_level(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_yearly_one_level_data):
    """Test pattern yearly one level."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = pattern_yearly_one_level_data['patterns']

    # test first issue
    assert holding.next_issue_display_text == '82 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == '83 2021'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == '108 2046'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == '120 2058'


def test_patterns_yearly_one_level_with_label(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_yearly_one_level_with_label_data):
    """Test pattern yearly one level with label."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = pattern_yearly_one_level_with_label_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Edition 29 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Edition 30 2021'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Edition 55 2046'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Edition 67 2058'


def test_patterns_yearly_two_times(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_yearly_two_times_data):
    """Test pattern yearly two times."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = pattern_yearly_two_times_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Jg. 8 2019 Nov.'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg. 9 2020 März'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg. 21 2032 Nov.'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Jg. 27 2038 Nov.'


def test_patterns_quarterly_two_levels(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_quarterly_two_levels_data):
    """Test pattern quarterly_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = pattern_quarterly_two_levels_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Jg. 20 Heft 1 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg. 20 Heft 2 2020'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg. 26 Heft 3 2026'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Jg. 29 Heft 3 2029'


def test_patterns_quarterly_two_levels_with_season(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_quarterly_two_levels_with_season_data):
    """Test pattern quarterly_two_levels_with_season."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_quarterly_two_levels_with_season_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == \
        'année 2019 no 277 2018 printemps'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'année 2019 no 278 2018 été'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == \
        'année 2025 no 303 2024 automne'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'année 2028 no 315 2027 automne'


def test_patterns_half_yearly_one_level(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_half_yearly_one_level_data):
    """Test pattern half_yearly_one_level."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_half_yearly_one_level_data['patterns']

    # test first issue
    assert holding.next_issue_display_text == 'N˚ 48 2019 printemps'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'N˚ 49 2019 automne'
    for r in range(13):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'N˚ 62 2026 printemps'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'N˚ 74 2032 printemps'


def test_patterns_bimonthly_every_two_months_one_level(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_bimonthly_every_two_months_one_level_data):
    """Test pattern quarterly_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_bimonthly_every_two_months_one_level_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == '47 2020 jan./fév.'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == '48 2020 mars/avril'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == '73 2024 mai/juin'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == '85 2026 mai/juin'


def test_patterns_half_yearly_two_levels(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_half_yearly_two_levels_data):
    """Test pattern half_yearly_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_half_yearly_two_levels_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Année 30 84 2020 June'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Année 30 85 2020 Dec.'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Année 43 110 2033 June'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Année 49 122 2039 June'


def test_bimonthly_every_two_months_two_levels(
        db, es_clear, holding_lib_martigny_w_patterns,
        pattern_bimonthly_every_two_months_two_levels_data):
    """Test pattern bimonthly_every_two_months_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_bimonthly_every_two_months_two_levels_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Jg 51 Nr 1 2020 Jan.'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg 51 Nr 2 2020 März'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg 55 Nr 3 2024 Mai'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Jg 57 Nr 3 2026 Mai'
