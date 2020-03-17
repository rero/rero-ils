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

import jinja2
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.documents.api import Document
from rero_ils.modules.errors import RecordValidationError
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item


def test_patterns_functions(holding_lib_martigny_w_patterns,
                            holding_lib_martigny):
    """Test holdings patterns functions."""
    # test no prediction for standard holdings record
    assert not holding_lib_martigny.increment_next_prediction()
    assert not holding_lib_martigny.next_issue_display_text
    assert not holding_lib_martigny.prediction_issues_preview(1)

    holding = holding_lib_martigny_w_patterns
    old_template = holding.get('patterns').get('template')
    # test invalid syntax for pattern templates
    template = 'no {{first_chronology.level_1}'
    holding['patterns']['template'] = template
    with pytest.raises(jinja2.exceptions.TemplateSyntaxError):
        assert holding.next_issue_display_text

    template = 'no {{unknown_chronology.level_1}}'
    holding['patterns']['template'] = template
    with pytest.raises(jinja2.exceptions.UndefinedError):
        assert holding.next_issue_display_text
    holding['patterns']['template'] = old_template


def test_patterns_quarterly_one_level(holding_lib_martigny_w_patterns):
    """Test holdings patterns annual two levels."""
    holding = holding_lib_martigny_w_patterns
    # test first issue
    assert holding.next_issue_display_text == 'no 61 mars 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'no 62 juin 2020'
    for r in range(11):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'no 73 mars 2023'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'no 85 mars 2026'


def test_patterns_yearly_one_level(
        holding_lib_martigny_w_patterns,
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
        holding_lib_martigny_w_patterns,
        pattern_yearly_one_level_with_label_data):
    """Test pattern yearly one level with label."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = pattern_yearly_one_level_with_label_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == '29 Edition 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == '30 Edition 2021'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == '55 Edition 2046'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == '67 Edition 2058'


def test_patterns_yearly_two_times(
        holding_lib_martigny_w_patterns,
        pattern_yearly_two_times_data):
    """Test pattern yearly two times."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = pattern_yearly_two_times_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Jg. 8 Nov. 2019'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg. 9 März 2020'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg. 21 Nov. 2032'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Jg. 27 Nov. 2038'


def test_patterns_quarterly_two_levels(
        holding_lib_martigny_w_patterns,
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
        holding_lib_martigny_w_patterns,
        pattern_quarterly_two_levels_with_season_data):
    """Test pattern quarterly_two_levels_with_season."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_quarterly_two_levels_with_season_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == \
        'année 2019 no 277 printemps 2018'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'année 2019 no 278 été 2018'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == \
        'année 2025 no 303 automne 2024'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'année 2028 no 315 automne 2027'


def test_patterns_half_yearly_one_level(
        holding_lib_martigny_w_patterns,
        pattern_half_yearly_one_level_data):
    """Test pattern half_yearly_one_level."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_half_yearly_one_level_data['patterns']

    # test first issue
    assert holding.next_issue_display_text == 'N˚ 48 printemps 2019'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'N˚ 49 automne 2019'
    for r in range(13):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'N˚ 62 printemps 2026'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'N˚ 74 printemps 2032'


def test_patterns_bimonthly_every_two_months_one_level(
        holding_lib_martigny_w_patterns,
        pattern_bimonthly_every_two_months_one_level_data):
    """Test pattern quarterly_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_bimonthly_every_two_months_one_level_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == '47 jan./fév. 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == '48 mars/avril 2020'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == '73 mai/juin 2024'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == '85 mai/juin 2026'


def test_patterns_half_yearly_two_levels(
        holding_lib_martigny_w_patterns,
        pattern_half_yearly_two_levels_data):
    """Test pattern half_yearly_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_half_yearly_two_levels_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Année 30 no 84 June 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Année 30 no 85 Dec. 2020'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Année 43 no 110 June 2033'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Année 49 no 122 June 2039'


def test_bimonthly_every_two_months_two_levels(
        holding_lib_martigny_w_patterns,
        pattern_bimonthly_every_two_months_two_levels_data):
    """Test pattern bimonthly_every_two_months_two_levels."""
    holding = holding_lib_martigny_w_patterns
    holding['patterns'] = \
        pattern_bimonthly_every_two_months_two_levels_data['patterns']
    # test first issue
    assert holding.next_issue_display_text == 'Jg 51 Nr 1 Jan. 2020'
    holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg 51 Nr 2 März 2020'
    for r in range(25):
        holding.increment_next_prediction()
    assert holding.next_issue_display_text == 'Jg 55 Nr 3 Mai 2024'
    # test preview
    issues = holding.prediction_issues_preview(13)
    assert issues[-1] == 'Jg 57 Nr 3 Mai 2026'


def test_pattern_preview_api(
        client, holding_lib_martigny_w_patterns, librarian_martigny_no_email):
    """Test holdings patterns preview api."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    holding = holding_lib_martigny_w_patterns
    # test preview by default 10 issues returned
    res = client.get(
        url_for(
            'api_holding.patterns_preview',
            holding_pid=holding.pid
        )
    )
    assert res.status_code == 200
    issues = get_json(res).get('issues')
    assert issues[0] == 'no 61 mars 2020'
    assert len(issues) == 10
    # test invalid size
    res = client.get(
        url_for(
            'api_holding.patterns_preview',
            holding_pid=holding.pid,
            size='no size'
        )
    )
    assert res.status_code == 200
    issues = get_json(res).get('issues')
    assert issues[0] == 'no 61 mars 2020'
    assert len(issues) == 10
    # test preview for a given size
    res = client.get(
        url_for(
            'api_holding.patterns_preview',
            holding_pid=holding.pid,
            size=13
        )
    )
    assert res.status_code == 200
    issues = get_json(res).get('issues')
    assert issues[12] == 'no 73 mars 2023'
    assert len(issues) == 13


def test_create_holdings_with_pattern(
        client, librarian_martigny_no_email, loc_public_martigny,
        journal, item_type_standard_martigny, document,
        json_header, holding_lib_martigny_data, pattern_yearly_one_level_data,
        holding_lib_martigny_w_patterns_data):
    """Test create holding type serial with patterns."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.hold_list'

    del holding_lib_martigny_data['pid']
    holding_lib_martigny_data['holdings_type'] = 'serial'
    res, _ = postdata(
        client,
        post_entrypoint,
        holding_lib_martigny_data
    )
    assert res.status_code == 403

    holding_lib_martigny_data['patterns'] = \
        pattern_yearly_one_level_data['patterns']

    # test will fail when creating a serial holding for a standard document.
    res, _ = postdata(
        client,
        post_entrypoint,
        holding_lib_martigny_data
    )
    assert res.status_code == 403

    # test will fail when creating a standard holding for a journal document.
    holding_lib_martigny_w_patterns_data['holdings_type'] = 'standard'
    del holding_lib_martigny_w_patterns_data['patterns']
    with pytest.raises(RecordValidationError):
        Holding.create(
            data=holding_lib_martigny_w_patterns_data,
            delete_pid=True,
            dbcommit=True,
            reindex=True)

    journal_pids = list(Document.get_all_serial_pids())
    assert journal_pids == [journal.pid]


def test_holding_pattern_preview_api(
        client, pattern_yearly_one_level_data,
        librarian_martigny_no_email):
    """Test holdings patterns preview api."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    patterns = pattern_yearly_one_level_data.get('patterns')
    # test preview by default 10 issues returned
    res, data = postdata(
        client,
        'api_holding.pattern_preview',
        dict(data=patterns, size=15)
    )
    assert res.status_code == 200

    issues = get_json(res).get('issues')
    assert issues[0] == '108 2046'
    assert len(issues) == 15

    # test invalid patterns
    del(patterns['values'])
    res, data = postdata(
        client,
        'api_holding.pattern_preview',
        dict(data=patterns)
    )
    assert res.status_code == 200

    issues = get_json(res).get('issues')
    assert issues == []
    assert len(issues) == 0


def test_automatic_item_creation_no_serials(
        client, json_header, holding_lib_martigny_w_patterns,
        item_lib_martigny_data, librarian_martigny_no_email):
    """Test automatically created items are not attached to serials."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = 'invenio_records_rest.item_list'
    res, _ = postdata(
        client,
        post_url,
        item_lib_martigny_data
    )
    assert res.status_code == 201
    item = Item.get_record_by_pid(item_lib_martigny_data.get('pid'))
    holding = Holding.get_record_by_pid(item.holding_pid)
    assert holding.pid != holding_lib_martigny_w_patterns.pid
    assert holding.location_pid == holding_lib_martigny_w_patterns.location_pid
    assert holding.get('circulation_category') == \
        holding_lib_martigny_w_patterns.get('circulation_category')
