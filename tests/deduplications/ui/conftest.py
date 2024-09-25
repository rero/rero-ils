# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Common pytest fixtures and plugins."""

import pytest


@pytest.fixture(scope="module")
def dedup_doc_data():
    """Deduplication document data."""
    yield {
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json",
        "type": [{"main_type": "docmaintype_book", "subtype": "docsubtype_other_book"}],
        "title": [
            {
                "type": "bf:Title",
                "mainTitle": [{"value": "La reine Berthe et sa fille"}],
                "subtitle": [
                    {"value": "une page du dixi\u00e8me si\u00e8cle offerte aux jeunes"}
                ],
            },
        ],
        "responsibilityStatement": [[{"value": "Nebehay, Christian Michael"}]],
        "contribution": [
            {
                "entity": {
                    "authorized_access_point": "Nebehay, Christian Michael",
                    "type": "bf:Person",
                },
                "role": ["aut"],
            }
        ],
        "language": [{"type": "bf:Language", "value": "fre"}],
        "provisionActivity": [
            {
                "type": "bf:Publication",
                "statement": [
                    {
                        "country": "sz",
                        "label": [{"value": "Lausanne"}],
                        "type": "bf:Place",
                    }
                ],
                "startDate": 1971,
            }
        ],
        "identifiedBy": [
            {
                "type": "bf:Isbn",
                "status": "invalid or cancelled",
                "value": "9782844267788",
            }
        ],
        "harvested": False,
        "fiction_statement": "unspecified",
        "adminMetadata": {"encodingLevel": "Minimal level"},
        "issuance": {"main_type": "rdami:1001", "subtype": "materialUnit"},
    }


@pytest.fixture(scope="module")
def create_app():
    """Create test app."""
    # create_ui
    from invenio_app.factory import create_ui

    return create_ui
