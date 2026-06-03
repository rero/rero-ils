# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2026 RERO
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

"""Organisation record extensions."""

from invenio_records.extensions import RecordExtension
from marshmallow_utils.html import sanitize_html

from .cache import delete_homepage_organisation_cache


class OrganisationHomepageSanitizerExtension(RecordExtension):
    """Sanitize homepage HTML blocks before saving an organisation."""

    def pre_create(self, record):
        """Sanitize homepage HTML blocks before creating an organisation."""
        self._sanitize(record)
        if record.model:
            record.model.data = record

    def pre_commit(self, record):
        """Sanitize homepage HTML blocks before committing an organisation."""
        self._sanitize(record)

    def post_commit(self, record):
        """Invalidate cached homepage data after saving an organisation."""
        if code := record.get("code"):
            delete_homepage_organisation_cache(code)

    def _sanitize(self, record):
        blocks = record.get("homepage", {}).get("blocks", {})
        for position in ("left", "center", "right"):
            for entry in blocks.get(position, []):
                if "value" in entry:
                    entry["value"] = sanitize_html(entry["value"])
