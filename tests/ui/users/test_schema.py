# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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
