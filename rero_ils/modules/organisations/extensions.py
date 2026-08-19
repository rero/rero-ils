# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Organisation record extensions."""

from invenio_records.extensions import RecordExtension
from marshmallow_utils.html import ALLOWED_HTML_ATTRS, sanitize_html

from .cache import delete_homepage_organisation_cache

# Allow the ``class`` attribute on every tag so the Bootstrap utility classes
# used in the homepage blocks (list-unstyled, text-center, ...) are preserved.
HOMEPAGE_ALLOWED_ATTRS = {**ALLOWED_HTML_ATTRS, "*": ["class"]}


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
                    entry["value"] = sanitize_html(entry["value"], attrs=HOMEPAGE_ALLOWED_ATTRS)
