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

"""Organisation extensions tests."""

from unittest.mock import patch

from rero_ils.modules.organisations.extensions import OrganisationHomepageSanitizerExtension


def test_sanitize_homepage_blocks(appctx):
    """Test homepage block sanitization on organisation record."""
    record = {
        "homepage": {
            "blocks": {
                "left": [
                    {"language": "fr", "value": '<p onclick="alert(1)">Texte</p>'},
                    {"language": "en", "value": "<script>bad()</script><p>Text</p>"},
                ],
                "center": [{"language": "fr", "value": "<style>p{}</style><h3>Centre</h3>"}],
                "right": [{"language": "fr", "value": "<unknown>Right</unknown>"}],
            }
        }
    }

    OrganisationHomepageSanitizerExtension()._sanitize(record)

    assert record["homepage"]["blocks"]["left"][0]["value"] == "<p>Texte</p>"
    assert record["homepage"]["blocks"]["left"][1]["value"] == "bad()<p>Text</p>"
    assert record["homepage"]["blocks"]["center"][0]["value"] == "p{}<h3>Centre</h3>"
    assert record["homepage"]["blocks"]["right"][0]["value"] == "Right"


def test_sanitize_homepage_blocks_without_homepage(appctx):
    """Test homepage block sanitization on record without homepage."""
    record = {"name": "Organisation"}

    OrganisationHomepageSanitizerExtension()._sanitize(record)

    assert record == {"name": "Organisation"}


@patch("rero_ils.modules.organisations.extensions.delete_homepage_organisation_cache")
def test_invalidate_homepage_cache_after_commit(cache_delete, appctx):
    """Test homepage cache invalidation after organisation commit."""
    OrganisationHomepageSanitizerExtension().post_commit({"code": "aoste"})

    cache_delete.assert_called_once_with("aoste")
