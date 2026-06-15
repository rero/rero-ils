# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Cache helpers for organisations."""

from invenio_cache import current_cache


def homepage_organisation_cache_key(viewcode):
    """Get organisation homepage current cache key by viewcode."""
    return f"organisation_by_viewcode:{viewcode}"


def delete_homepage_organisation_cache(viewcode):
    """Delete cached organisation homepage data by viewcode."""
    return current_cache.delete(homepage_organisation_cache_key(viewcode))
