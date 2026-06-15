# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Babel extractors tests."""

from rero_ils.modules.babel_extractors import extract_json


def test_babel_extractors_extract_json(babel_filehandle):
    """Test extract json."""
    translations = extract_json(
        fileobj=babel_filehandle,
        keywords=None,
        comment_tags=None,
        options={"keys_to_translate": "['title']"},
    )
    assert translations == [
        (4, "gettext", "Organisation", []),
        (14, "gettext", "Schema", []),
        (20, "gettext", "Organisation ID", []),
        (24, "gettext", "Name", []),
        (1, "gettext", "day(s)", ["Line unknown"]),
    ]
