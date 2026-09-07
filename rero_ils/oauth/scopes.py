# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""OAuth server scopes."""

from flask_babel import lazy_gettext as _
from invenio_oauth2server.models import Scope

fullname = Scope("fullname", help_text=_("Full name"), group="User")
birthdate = Scope("birthdate", help_text=_("Birth date"), group="User")
expiration_date = Scope("expiration_date", help_text=_("Expiration date"), group="User")
institution = Scope("institution", help_text=_("Organisation"), group="User")
patron_type = Scope("patron_type", help_text=_("Patron type"), group="User")
patron_types = Scope("patron_types", help_text=_("Network, patron type, and expiration date (regrouped)"), group="User")
