# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests serializer response factories."""

from flask import Flask

from rero_ils.modules.serializers.response import search_responsify_file


def test_search_responsify_file_resets_serializer():
    """Test cached serializers are reset before each file export."""
    calls = []

    class Serializer:
        def reset(self):
            calls.append("reset")

        def serialize_search(self, *args, **kwargs):
            calls.append("serialize")
            return "content"

    view = search_responsify_file(Serializer(), "text/plain", "txt")

    with Flask(__name__).app_context():
        first_response = view(None, None)
        second_response = view(None, None)

    assert first_response.get_data(as_text=True) == "content"
    assert second_response.get_data(as_text=True) == "content"
    assert calls == ["reset", "serialize", "reset", "serialize"]
