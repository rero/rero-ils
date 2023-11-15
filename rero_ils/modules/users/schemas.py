# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Models for RERO-ILS users."""
from marshmallow import Schema, fields


class UserProfile(Schema):
    """A custom user profile schema."""

    last_name = fields.String()
    """Last name of person."""

    first_name = fields.String()
    """First name of person."""

    gender = fields.String()
    """Gender of person."""

    birth_date = fields.Date()
    """Birth date of person."""

    street = fields.String()
    """Street address of person."""

    postal_code = fields.String()
    """Postal code address of person."""

    city = fields.String()
    """City address of person."""

    country = fields.String()
    """Country address of person."""

    home_phone = fields.String()
    """Home phone number of person."""

    business_phone = fields.String()
    """Business phone number of person."""

    mobile_phone = fields.String()
    """Mobile phone number of person."""

    other_phone = fields.String()
    """Other phone number of person."""

    keep_history = fields.Boolean()
    """Boolean stating to keep loan history or not."""
