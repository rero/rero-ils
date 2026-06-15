# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E test of the front page."""

from flask import url_for


def test_frontpage(live_server, browser):
    """Test retrieval of front page."""
    browser.get(url_for("rero_ils.index", _external=True))
    assert browser.find_element_by_tag_name("h1").text == "Get into your library"
