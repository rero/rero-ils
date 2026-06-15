# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Simple test of version import."""


def test_version():
    """Test version import."""
    from rero_ils import __version__

    assert __version__
