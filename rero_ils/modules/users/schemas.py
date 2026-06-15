# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
