# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2024 RERO
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

"""Migration Record tests."""

from rero_ils.modules.deduplications.api import Deduplication


def test_deduplications_title_score():
    """Test the deduplication title score."""

    def create(title):
        return {
            "title": [
                {"type": "bf:Title", "mainTitle": [{"value": title}], "_text": title}
            ]
        }

    document = create("La reine Berthe et sa fille")
    assert Deduplication.get_title_score(document, document) == 1
    for title in [
        "la reine Berthe et sa fille",
        "La  reine Berthe et sa fille",
        "La reine Berthe & sa fille",
        "La reine Berthe sa fille",
        "La reine Berthe",
    ]:
        candidate = create(title)
        assert Deduplication.get_title_score(document, candidate) > 0

    assert Deduplication.get_title_score(document, create("")) == 0
    assert Deduplication.get_title_score(document, create("A title.")) == 0


def test_series_statement_score():
    """Test the series statement score."""

    def create(statement):
        return {
            "seriesStatement": [
                {"_text": [{"language": "default", "value": statement}]}
            ]
        }

    document = create("harry potter")
    assert Deduplication.get_series_statement_score(document, document) == 1
    assert (
        Deduplication.get_series_statement_score(document, create("Harry   Potter "))
        == 1
    )
    # needs exact match
    assert (
        Deduplication.get_series_statement_score(document, create("hary potter")) == 0
    )
    assert Deduplication.get_series_statement_score(document, {}) == 0
    assert Deduplication.get_series_statement_score({}, {}) is None
    assert Deduplication.get_series_statement_score({}, document) == 0


def test_edition_statement_score():
    """Test the edition statement score."""

    def create(statement):
        return {
            "editionStatement": [
                {"_text": [{"language": "default", "value": statement}]}
            ]
        }

    document = create("2e éd")
    assert Deduplication.get_edition_statement_score(document, document) == 1
    assert Deduplication.get_edition_statement_score(document, create("2e ed ")) == 1
    # needs exact match
    assert (
        Deduplication.get_edition_statement_score(document, create("2éme édition")) == 0
    )
    assert Deduplication.get_edition_statement_score(document, {}) == 0
    assert Deduplication.get_edition_statement_score({}, {}) is None
    assert Deduplication.get_edition_statement_score({}, document) == 0


def test_document_type_score():
    """Test the document type score."""

    def create(types):
        return {"type": [{"main_type": t} for t in types]}

    assert (
        Deduplication.get_doc_type_score(
            create(["docmaintype_article"]), create(["docmaintype_article"])
        )
        == 1
    )
    assert (
        Deduplication.get_doc_type_score(
            create(["docmaintype_article"]), create(["docmaintype_book"])
        )
        == 0
    )
    assert (
        Deduplication.get_doc_type_score(
            create(["docmaintype_article", "docmaintype_book"]),
            create(["docmaintype_article"]),
        )
        == 1
    )
    assert (
        Deduplication.get_doc_type_score(
            create(["docmaintype_article"]),
            create(["docmaintype_article", "docmaintype_book"]),
        )
        == 1
    )


def test_publication_date_score():
    """Test the publication date score."""
    assert (
        Deduplication.get_publication_date_score(
            {"sort_date_old": 2024}, {"sort_date_old": 2024}
        )
        == 1
    )
    assert (
        Deduplication.get_publication_date_score(
            {"sort_date_old": 2024}, {"sort_date_old": 2023}
        )
        == 0
    )
    assert Deduplication.get_publication_date_score({"sort_date_old": 2024}, {}) == 0
    assert Deduplication.get_publication_date_score({}, {"sort_date_old": 2023}) == 0
    assert Deduplication.get_publication_date_score({}, {}) == 1


def test_provision_activity_score():
    """Test the provision activity score."""

    def create(prov):
        return {
            "provisionActivity": [{"_text": [{"language": "default", "value": prov}]}]
        }

    document = create("Paris : M. Lévy, 1860")
    assert Deduplication.get_provision_activity_score(document, document) == 1
    assert (
        Deduplication.get_provision_activity_score(
            document, create("Paris :  m. Levy, 1860")
        )
        == 1
    )
    assert (
        Deduplication.get_provision_activity_score(document, create("Paris, 1860")) > 0
    )


def test_extent_score():
    """Test the extent score."""
    assert Deduplication.get_extent_score({"extent": "32 p."}, {"extent": "32 p."}) == 1
    assert Deduplication.get_extent_score({"extent": "32 p."}, {}) == 0
    assert Deduplication.get_extent_score({}, {"extent": "32 p."}) == 0
    assert Deduplication.get_extent_score({}, {}) == 1
    assert Deduplication.get_extent_score({"extent": "32 p."}, {"extent": "31 p."}) == 0
    assert (
        Deduplication.get_extent_score(
            {"extent": "32 p., vol. 45"}, {"extent": "32 p."}
        )
        == 0.5
    )
    assert (
        Deduplication.get_extent_score(
            {"extent": "32 p., vol. 45"}, {"extent": "volume 45, 32 p."}
        )
        == 1
    )


def test_responsibility_score():
    """Test the responsibility statement score."""

    def create(statement):
        return {"responsibilityStatement": [[{"value": statement}]]}

    document = create("J. K.  Rowling")
    assert Deduplication.get_responsibility_score(document, document) == 1
    assert Deduplication.get_responsibility_score(document, {}) == 0
    assert Deduplication.get_responsibility_score({}, document) == 0
    assert Deduplication.get_responsibility_score({}, {}) == 1
    assert (
        Deduplication.get_responsibility_score(document, create("J. K. Rowling")) == 1
    )
    assert Deduplication.get_responsibility_score(document, create("JK Rowling")) > 0
    assert Deduplication.get_responsibility_score(document, create("Harry Potter")) == 0


def test_identifier_score():
    """Test the identifier score."""
    document = {"identifiedBy": [{"type": "bf:Isbn", "value": "9780674993167"}]}
    assert Deduplication.get_identifier_score(document, document) == 1
    assert Deduplication.get_identifier_score(document, {}) == 0
    assert Deduplication.get_identifier_score({}, document) == 0
    assert Deduplication.get_identifier_score({}, {}) is None

    candidate = {
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9780674993167"},
            {"type": "bf:Ean", "value": "9780674993167"},
        ]
    }
    assert Deduplication.get_identifier_score(document, candidate) == 1
    assert Deduplication.get_identifier_score(candidate, document) == 1

    candidate = {
        "identifiedBy": [
            {"type": "bf:Ean", "value": "9780674993167"},
        ]
    }
    assert Deduplication.get_identifier_score(document, candidate) == 0
    assert Deduplication.get_identifier_score(candidate, document) == 0

    # bf:Local should be ignored
    document = {
        "identifiedBy": [
            {"type": "bf:Local", "value": "1"},
        ]
    }
    assert Deduplication.get_identifier_score(document, document) is None
