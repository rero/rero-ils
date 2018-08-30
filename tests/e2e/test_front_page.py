"""E2E test of the front page."""

from flask import url_for


def test_frontpage(live_server, browser):
    """Test retrieval of front page."""
    browser.get(url_for('invenio_theme_frontpage.index', _external=True))
    assert "Welcome to reroils-app." == browser.find_element_by_class_name(
        'marketing').find_element_by_tag_name('h1').text
