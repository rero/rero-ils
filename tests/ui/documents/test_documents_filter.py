# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document filters tests."""

from unittest import mock

from rero_ils.modules.documents.views import (
    babeltheque_enabled_view,
    contribution_format,
    doc_entity_label,
    get_cover_art,
    get_first_isbn,
    main_title_text,
    part_of_format,
    provision_activity,
    provision_activity_publication,
)
from rero_ils.modules.entities.models import EntityType


def test_provision_activity():
    """Test preprocess provision activity."""
    provisions = [
        {
            "_text": [{"language": "default", "value": "Paris : Ed. de Minuit, 1988"}],
            "place": [{"country": "fr", "type": "bf:Place"}],
            "startDate": 1988,
            "statement": [
                {"label": [{"value": "Paris"}], "type": "bf:Place"},
                {"label": [{"value": "Ed. de Minuit"}], "type": "bf:Agent"},
                {"label": [{"value": "1988"}], "type": "Date"},
            ],
            "type": "bf:Publication",
        },
        {
            "_text": [{"language": "default", "value": "Martigny : Alex Morgan, 2010"}],
            "startDate": 1998,
            "statement": [
                {"label": [{"value": "Martigny"}], "type": "bf:Place"},
                {"label": [{"value": "Alex Morgan"}], "type": "bf:Agent"},
                {"label": [{"value": "2010"}], "type": "Date"},
            ],
            "type": "bf:Distribution",
        },
        {
            "_text": [
                {
                    "language": "default",
                    "value": "Will Edwards, 2010 ; Paris ; Martigny",
                }
            ],
            "startDate": 1990,
            "statement": [
                {"label": [{"value": "Will Edwards"}], "type": "bf:Agent"},
                {"label": [{"value": "2010"}], "type": "Date"},
                {"label": [{"value": "Paris"}], "type": "bf:Place"},
                {"label": [{"value": "Martigny"}], "type": "bf:Place"},
            ],
            "type": "bf:Distribution",
        },
        {
            "_text": [{"language": "default", "value": ""}],
            "original_date": 2010,
            "place": [{"country": "xx", "type": "bf:Place"}],
            "startDate": 1989,
            "type": "bf:Manufacture",
        },
    ]
    result = {
        "bf:Publication": [{"language": "default", "value": "Paris : Ed. de Minuit, 1988"}],
        "bf:Distribution": [
            {"language": "default", "value": "Martigny : Alex Morgan, 2010"},
            {"language": "default", "value": "Will Edwards, 2010 ; Paris ; Martigny"},
        ],
    }
    assert result == provision_activity(provisions)


def test_provision_activity_publication():
    """Test extract only publication on provision activity."""
    provisions = {
        "bf:Publication": [{"language": "default", "value": "Paris : Ed. de Minuit, 1988"}],
        "bf:Distribution": [
            {"language": "default", "value": "Martigny : Alex Morgan, 2010"},
            {"language": "default", "value": "Will Edwards, 2010 ; Paris ; Martigny"},
        ],
    }
    result = {"bf:Publication": [{"language": "default", "value": "Paris : Ed. de Minuit, 1988"}]}
    assert result == provision_activity_publication(provisions)


def test_contribution_format(db, entity_organisation):
    """Test contribution format."""
    entity = entity_organisation
    contributions = [
        {
            "entity": {
                "authorized_access_point": "author_def",
                "authorized_access_point_fr": "author_fr",
            }
        }
    ]

    # ---- Textual contribution
    # With english language
    link_part = "/global/search/documents?q=contribution.entity.authorized_access_point_en:%22author_def%22"
    assert link_part in contribution_format(contributions, "en", "global")

    # With french language
    link_part = "/global/search/documents?q=contribution.entity.authorized_access_point_fr:%22author_fr%22"
    assert link_part in contribution_format(contributions, "fr", "global")

    # ---- Remote contribution
    contributions = [{"entity": {"pid": entity.pid}}]
    link_part = f"/global/search/documents?q=contribution.entity.pids.{entity.resource_type}:{entity.pid}"
    assert link_part in contribution_format(contributions, "en", "global")


def test_part_of_format(document_with_issn, document2_with_issn, document_sion_items):
    """Test 'part of' format."""
    # Label Series with numbering
    part_of = {
        "document": {"$ref": "https://bib.rero.ch/api/documents/doc5"},
        "numbering": [{"year": "1818", "volume": 2704, "issue": "1", "pages": "55"}],
    }
    result = {
        "document_pid": "doc5",
        "label": "Series",
        "numbering": ["1818, vol. 2704, nr. 1, p. 55"],
        "title": "Manuales del Africa espa\u00f1ola",
    }
    assert result == part_of_format(part_of)
    # Label Journal with numbering
    part_of = {
        "document": {"$ref": "https://bib.rero.ch/api/documents/doc6"},
        "numbering": [{"year": "1818", "volume": 2704, "issue": "1", "pages": "55"}],
    }
    result = {
        "document_pid": "doc6",
        "label": "Journal",
        "numbering": ["1818, vol. 2704, nr. 1, p. 55"],
        "title": "Nota bene",
    }
    assert result == part_of_format(part_of)
    # Label Published in without numbering
    part_of = {"document": {"$ref": "https://bib.rero.ch/api/documents/doc3"}}
    result = {
        "document_pid": "doc3",
        "label": "Published in",
        "title": "La reine Berthe et son fils",
    }
    assert result == part_of_format(part_of)


def test_main_title_text():
    """Test extract only main title."""
    title = [
        {"mainTitle": [{"value": "J. Am. Med. Assoc."}], "type": "bf:AbbreviatedTitle"},
        {"mainTitle": [{"value": "J Am Med Assoc"}], "type": "bf:KeyTitle"},
        {
            "_text": "Journal of the American medical association",
            "mainTitle": [{"value": "Journal of the American medical association"}],
            "type": "bf:Title",
        },
    ]
    extract = main_title_text(title)
    assert len(extract) == 1
    assert extract[0].get("_text") is not None


def test_doc_entity_label_filter(entity_person, local_entity_person):
    """Test entity label filter."""

    # Remote entity
    remote_pid = entity_person["idref"]["pid"]
    data = {
        "entity": {
            "$ref": f"https://mef.rero.ch/api/concepts/idref/{remote_pid}",
            "pid": remote_pid,
        }
    }
    entity_type, value, label = doc_entity_label(data["entity"], "fr")
    assert entity_type == "remote"
    assert value == "ent_pers"
    assert label == "Loy, Georg, 1885-19.."

    # Local entity
    pid = local_entity_person["pid"]
    data = {"entity": {"$ref": f"https://bib.rero.ch/api/local_entities/{pid}"}}
    entity_type, value, label = doc_entity_label(data["entity"], "fr")
    assert entity_type == "local"
    assert value == "locent_pers"
    assert label == "Loy, Georg (1881-1968)"

    entity_type, value, label = doc_entity_label(data["entity"], "en")
    assert entity_type == "local"
    assert value == "locent_pers"
    assert label == "Loy, Georg (1881-1968)"

    # Textual
    data = {"entity": {"authorized_access_point": "subject topic"}}
    entity_type, value, label = doc_entity_label(data["entity"], None)
    assert entity_type == "textual"
    assert value == "subject topic"
    assert label == "subject topic"

    entity_type, value, label = doc_entity_label(data["entity"], "fr")
    assert entity_type == "textual"
    assert value == "subject topic"
    assert label == "subject topic"

    # Textual with subdivision
    data["entity"]["subdivisions"] = [
        {"entity": {"authorized_access_point": "Sub 1", "type": EntityType.TOPIC}},
        {"entity": {"authorized_access_point": "Sub 2", "type": EntityType.TOPIC}},
    ]
    entity_type, value, label = doc_entity_label(data["entity"], "fr")
    assert entity_type == "textual"
    assert value == "subject topic"
    assert label == "subject topic - Sub 1 - Sub 2"


def test_babeltheque_enabled_view():
    """Check enabled view for babeltheque."""

    class CurrentApp:
        """Current app mock."""

        config = {"RERO_ILS_BABELTHEQUE_ENABLED_VIEWS": ["global"]}

    with mock.patch("rero_ils.modules.documents.views.current_app", CurrentApp):
        assert babeltheque_enabled_view("global")
        assert not babeltheque_enabled_view("foo")


def test_get_first_isbn():
    """Get the first isbn on identifiedBy field."""
    record = {
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9782501053006"},
            {"type": "bf:Isbn", "value": "9782501033671"},
        ]
    }
    assert get_first_isbn(record) == "9782501053006"
    record = {"identifiedBy": []}
    assert None is get_first_isbn(record)


def test_get_cover_art_from_electronic_locator():
    """Test get_cover_art returns URL from electronicLocator."""
    record = {
        "electronicLocator": [
            {
                "url": "http://example.com/cover.jpg",
                "type": "relatedResource",
                "content": "coverImage",
            }
        ]
    }
    assert get_cover_art(record) == "http://example.com/cover.jpg"


def test_get_cover_art_from_electronic_locator_multiple():
    """Test get_cover_art returns first matching coverImage."""
    record = {
        "electronicLocator": [
            {
                "url": "http://example.com/other.jpg",
                "type": "relatedResource",
                "content": "fullText",
            },
            {
                "url": "http://example.com/cover1.jpg",
                "type": "relatedResource",
                "content": "coverImage",
            },
            {
                "url": "http://example.com/cover2.jpg",
                "type": "relatedResource",
                "content": "coverImage",
            },
        ]
    }
    # Should return the first coverImage
    assert get_cover_art(record) == "http://example.com/cover1.jpg"


def test_get_cover_art_from_isbn():
    """Test get_cover_art returns None when only ISBN is present (no electronicLocator)."""
    record = {
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9781234567890"},
            {"type": "bf:Issn", "value": "1234-5678"},
        ]
    }
    assert get_cover_art(record) is None


def test_get_cover_art_from_multiple_isbns():
    """Test get_cover_art returns None when only ISBNs are present (no electronicLocator)."""
    record = {
        "identifiedBy": [
            {"type": "bf:Isbn", "value": "9782222222222"},
            {"type": "bf:Isbn", "value": "9781111111111"},
        ]
    }
    assert get_cover_art(record) is None


def test_get_cover_art_no_isbn_no_electronic_locator():
    """Test get_cover_art returns None when no ISBN or electronicLocator."""
    record = {"identifiedBy": [{"type": "bf:Issn", "value": "1234-5678"}]}

    assert get_cover_art(record) is None


def test_get_cover_art_isbn_no_thumbnail_found():
    """Test get_cover_art returns None when no matching electronicLocator exists."""
    record = {"identifiedBy": [{"type": "bf:Isbn", "value": "9780000000000"}]}

    assert get_cover_art(record) is None


def test_get_cover_art_electronic_locator_wrong_type():
    """Test get_cover_art returns None when electronicLocator has wrong type."""
    record = {
        "electronicLocator": [
            {
                "url": "http://example.com/cover.jpg",
                "type": "versionOfResource",
                "content": "coverImage",
            }
        ]
    }
    assert get_cover_art(record) is None


def test_get_cover_art_electronic_locator_wrong_content():
    """Test get_cover_art returns None when electronicLocator has wrong content."""
    record = {
        "electronicLocator": [
            {
                "url": "http://example.com/fulltext.pdf",
                "type": "relatedResource",
                "content": "fullText",
            }
        ]
    }
    assert get_cover_art(record) is None


def test_get_cover_art_empty_record():
    """Test get_cover_art with empty record."""
    record = {}

    assert get_cover_art(record) is None


def test_get_cover_art_thumbnail_url_parameters():
    """Test get_cover_art returns the URL from a matching electronicLocator."""
    record = {
        "electronicLocator": [
            {"url": "https://covers.example.com/cover.jpg", "type": "relatedResource", "content": "coverImage"}
        ]
    }
    assert get_cover_art(record) == "https://covers.example.com/cover.jpg"
