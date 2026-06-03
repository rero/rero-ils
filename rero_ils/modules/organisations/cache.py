# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2026 RERO
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

"""Cache helpers for organisations."""

from invenio_cache import current_cache


def homepage_organisation_cache_key(viewcode):
    """Get organisation homepage current cache key by viewcode."""
    return f"organisation_by_viewcode:{viewcode}"


def delete_homepage_organisation_cache(viewcode):
    """Delete cached organisation homepage data by viewcode."""
    return current_cache.delete(homepage_organisation_cache_key(viewcode))
