# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""OAuth server scopes."""

from invenio_oauth2server.models import Scope

fullname = Scope("fullname", help_text="Full name", group="User")
birthdate = Scope("birthdate", help_text="Birthdate", group="User")
expiration_date = Scope("expiration_date", help_text="Expiration date", group="User")
institution = Scope("institution", help_text="Institution", group="User")
patron_type = Scope("patron_type", help_text="Patron type", group="User")
patron_types = Scope("patron_types", help_text="Patron types (deprecated)", group="User")
