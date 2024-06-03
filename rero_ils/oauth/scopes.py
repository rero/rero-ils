# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""OAuth server scopes."""

from invenio_oauth2server.models import Scope

fullname = Scope("fullname", help_text="Full name", group="User")
birthdate = Scope("birthdate", help_text="Birthdate", group="User")
institution = Scope("institution", help_text="Institution", group="User")
expiration_date = Scope("expiration_date", help_text="Expiration date", group="User")
patron_type = Scope("patron_type", help_text="Patron type", group="User")
patron_types = Scope("patron_types", help_text="Patron types", group="User")
