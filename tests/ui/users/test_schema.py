# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Schema for users."""

import pytest
from invenio_accounts.models import User


def test_custom_schema(app):
    """Test register form."""
    user = User(email="admin@inveniosoftware.org")
    user.user_profile = {
        "first_name": "Louis",
        "last_name": "Roduit",
        "gender": "male",
        "birth_date": "1947-06-07",
        "street": "Avenue Leopold-Robert, 13",
        "postal_code": "1920",
        "city": "Martigny",
        "country": "sz",
        "home_phone": "+41324993156",
        "business_phone": "+41324993156",
        "mobile_phone": "+41324993156",
        "other_phone": "+41324993156",
    }
    assert user
    with pytest.raises(ValueError):
        user.user_profile = {
            "username": "admin",
        }
