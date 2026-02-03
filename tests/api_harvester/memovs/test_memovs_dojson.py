# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test api harvester memovs dojson."""

from unittest.mock import Mock, patch

from rero_ils.modules.api_harvester.memovs.dojson.json import Transformation
from rero_ils.modules.api_harvester.memovs.dojson.json.model import normalize_newlines

_REQUESTS_SESSION_PATCH = "rero_ils.modules.api_harvester.memovs.dojson.json.model.requests_retry_session"


def _mock_mef_found(mock_session):
    def _get(url, **kwargs):
        idref_id = url.split("idref:")[-1]
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"idref": {"pid": idref_id}}
        return resp

    mock_session.return_value.get.side_effect = _get


def _mock_mef_not_found(mock_session):
    resp = Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {}
    mock_session.return_value.get.return_value = resp


def test_normalize_agent_type(app):
    """Test _normalize_agent_type function."""
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)

    # Test bf:Organization normalization to bf:Organisation
    assert transformation._normalize_agent_type("bf:Organization") == "bf:Organisation"

    # Test that other types remain unchanged
    assert transformation._normalize_agent_type("bf:Person") == "bf:Person"
    assert transformation._normalize_agent_type("bf:Organisation") == "bf:Organisation"
    assert transformation._normalize_agent_type("bf:Topic") == "bf:Topic"
    assert transformation._normalize_agent_type("bf:Place") == "bf:Place"
    assert transformation._normalize_agent_type("bf:Temporal") == "bf:Temporal"
    assert transformation._normalize_agent_type("bf:Work") == "bf:Work"


def test_trans_constants(app):
    """Test transformation constants."""
    _rda = "http://rdaregistry.info/termList/RDAContentType/"

    # Common field checks on one record
    data = {"bf:content": {"@id": f"{_rda}rdaco:1023", "rdfs:label": "image animée bidimensionnelle"}}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_constants()
    assert transformation.json["harvested"] is True
    assert transformation.json["issuance"] == {"main_type": "rdami:1001", "subtype": "materialUnit"}
    assert transformation.json["fiction_statement"] == "unspecified"
    assert transformation.json["type"] == [{"main_type": "docmaintype_movie_series", "subtype": "docsubtype_movie"}]

    # All RDA code → RERO-ILS type mappings
    cases = [
        ("rdaco:1023", [{"main_type": "docmaintype_movie_series", "subtype": "docsubtype_movie"}]),
        ("rdaco:1011", [{"main_type": "docmaintype_audio", "subtype": "docsubtype_music"}]),
        ("rdaco:1012", [{"main_type": "docmaintype_audio", "subtype": "docsubtype_sound"}]),
        ("rdaco:1013", [{"main_type": "docmaintype_audio", "subtype": "docsubtype_recorded_words"}]),
        ("rdaco:1014", [{"main_type": "docmaintype_image", "subtype": "docsubtype_photography"}]),
    ]
    for code, expected_type in cases:
        data = {"bf:content": {"@id": f"{_rda}{code}"}}
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_constants()
        assert transformation.json["type"] == expected_type, f"Wrong type for {code}"

    # Unknown code falls back to docmaintype_other
    data = {"bf:content": {"@id": f"{_rda}rdaco:9999"}}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_constants()
    assert transformation.json["type"] == [{"main_type": "docmaintype_other"}]

    # Missing bf:content also gives docmaintype_other
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)
    transformation.trans_constants()
    assert transformation.json["type"] == [{"main_type": "docmaintype_other"}]


def test_trans_pid(app):
    """Test transformation pid."""
    data = {"@id": "urn:avn:75864"}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_pid()
    assert transformation.json == {"pid": "(MEMOVS)75864"}


def test_trans_identified_by(app):
    """Test transformation identifiedBy."""
    data = {
        "@id": "urn:avn:75864",
        "bf:identifier": [
            {
                "@type": "bf:Identifier",
                "rdf:value": "VT-MA-TH5-1999-1",
                "bf:noteType": "local",
            },
            {
                "@type": "bf:Identifier",
                "rdf:value": "VS-C-002",
                "bf:noteType": "shelfMark",
            },
            {
                # Excluded: cote identifiers only feed the item's call_number, not identifiedBy
                "@type": "bf:Identifier",
                "rdf:value": "037ph-00038a-h",
                "bf:noteType": "cote",
            },
        ],
        # bf:hasPart call numbers are handled by ApiMemovs.sync_items, not by this transformation
        "bf:hasPart": {
            "@type": "bf:Instance",
            "bf:identifier": [{"@type": "bf:Local", "rdf:value": "037ph-00038a-h"}],
        },
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_identified_by()
    assert transformation.json == {
        "identifiedBy": [
            {"source": "MEMOVS", "type": "bf:Local", "value": "(MEMOVS)75864"},
            {"source": "LOCAL", "type": "bf:Local", "value": "VT-MA-TH5-1999-1"},
            {"source": "SHELFMARK", "type": "bf:Local", "value": "VS-C-002"},
        ],
    }


def test_trans_title(app):
    """Test transformation title."""
    data = {
        "bf:title": {
            "@type": "bf:Title",
            "bf:mainTitle": "L'hiver au Lötschental",
            "rdfs:label": "L'hiver au Lötschental",
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_title()
    assert transformation.json == {"title": [{"mainTitle": [{"value": "L'hiver au Lötschental"}], "type": "bf:Title"}]}


def test_trans_contribution(app):
    """Test transformation contribution with type validation."""
    # Local entity (no idref @id): authorized_access_point used
    data = {
        "bf:contribution": [
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "Binder, Pantaléon"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/pht"},
            },
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "Schmid, Albert"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/drt"},
            },
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_contribution()
    assert transformation.json == {
        "contribution": [
            {"entity": {"authorized_access_point": "Binder, Pantaléon", "type": "bf:Person"}, "role": ["pht"]},
            {"entity": {"authorized_access_point": "Schmid, Albert", "type": "bf:Person"}, "role": ["drt"]},
        ],
    }

    # Organisation type
    data = {
        "bf:contribution": [
            {
                "bf:agent": {"@type": "bf:Organisation", "rdfs:label": "Médiathèque Valais"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/fnd"},
            },
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_contribution()
    assert transformation.json["contribution"][0]["entity"] == {
        "authorized_access_point": "Médiathèque Valais",
        "type": "bf:Organisation",
    }

    # bf:Organization (US spelling) normalises to bf:Organisation
    data = {
        "bf:contribution": [
            {
                "bf:agent": {"@type": "bf:Organization", "rdfs:label": "Test Organization"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/fnd"},
            },
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_contribution()
    assert transformation.json["contribution"][0]["entity"]["type"] == "bf:Organisation"

    # Unknown role code falls back to 'ctb' (both entries kept)
    data = {
        "bf:contribution": [
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "Valid Person"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/pht"},
            },
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "Unknown Role Person"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/xxx"},
            },
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_contribution()
    assert len(transformation.json["contribution"]) == 2
    assert transformation.json["contribution"][0]["role"] == ["pht"]
    assert transformation.json["contribution"][1]["role"] == ["ctb"]

    # Agent label is a URL — skipped with warning (bad source data)
    data = {
        "@id": "urn:avn:12345",
        "bf:contribution": [
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "Valid Person"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/pht"},
            },
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "http://msav.memovs.ch/images/save.gif"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/ctb"},
            },
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_contribution()
    assert len(transformation.json["contribution"]) == 1
    assert transformation.json["contribution"][0]["entity"]["authorized_access_point"] == "Valid Person"

    # Invalid entity type skipped
    data = {
        "@id": "urn:avn:12345",
        "bf:contribution": [
            {
                "bf:agent": {"@type": "bf:Person", "rdfs:label": "Valid Person"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/pht"},
            },
            {
                "bf:agent": {"@type": "bf:Topic", "rdfs:label": "Invalid Topic as Agent"},
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/ctb"},
            },
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_contribution()
    assert len(transformation.json["contribution"]) == 1
    assert transformation.json["contribution"][0]["entity"]["type"] == "bf:Person"


def test_trans_provision_activity(app):
    """Test transformation provisionActivity."""
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "bf:date": {"rdf:value": "1950"},
            "bf:agent": {"@type": "bf:Organisation", "rdfs:label": "Cinémathèque suisse"},
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    assert "provisionActivity" in transformation.json
    assert len(transformation.json["provisionActivity"]) == 1
    prov = transformation.json["provisionActivity"][0]
    assert prov["startDate"] == 1950
    # type is taken from the source @type
    assert prov["type"] == "bf:Publication"
    assert len(prov["statement"]) == 2
    assert any(s.get("label", [{}])[0].get("value") == "Cinémathèque suisse" for s in prov["statement"])
    assert any(s.get("label", [{}])[0].get("value") == "1950" for s in prov["statement"])

    # Test with date in startDate field, no bf:agent in the source: no agent statement is fabricated
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "startDate": "1950-1960",
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["startDate"] == 1950
    assert prov["type"] == "bf:Publication"
    assert prov["statement"] == [{"label": [{"value": "1950"}], "type": "Date"}]

    # a non-default @type is passed through unchanged; the structured place
    # (country) is only added for bf:Publication, but the bf:Place statement
    # (town name) is still imported
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Production",
            "startDate": "1950-1960",
            "bf:place": {"@type": "bf:Place", "rdfs:label": "Sion"},
            "bf:agent": {"@type": "bf:Organisation", "rdfs:label": "Médiathèque Valais"},
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["startDate"] == 1950
    assert prov["type"] == "bf:Production"
    assert "place" not in prov
    assert any(s.get("label", [{}])[0].get("value") == "Sion" for s in prov["statement"])
    assert any(s.get("label", [{}])[0].get("value") == "Médiathèque Valais" for s in prov["statement"])
    assert any(s.get("label", [{}])[0].get("value") == "1950" for s in prov["statement"])

    # bf:agent label is used as-is, including bracketed cataloguing placeholders
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "startDate": "2023",
            "bf:agent": {"@type": "bf:Agent", "rdfs:label": "[éditeur non identifié]"},
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["statement"] == [
        {"label": [{"value": "[éditeur non identifié]"}], "type": "bf:Agent"},
        {"label": [{"value": "2023"}], "type": "Date"},
    ]

    # bf:agent present but with no usable label: no agent statement is fabricated
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "startDate": "2023",
            "bf:agent": {"@type": "bf:Agent"},
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["statement"] == [{"label": [{"value": "2023"}], "type": "Date"}]

    # bf:date.rdfs:label is used as-is for the Date statement, even as a full date
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "bf:date": {"rdfs:label": "22 septembre 1939", "rdf:value": "1939-09-22"},
            "startDate": "1939-09-22",
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["startDate"] == 1939
    assert prov["statement"] == [{"label": [{"value": "22 septembre 1939"}], "type": "Date"}]

    # bf:place is mapped to a bf:Place statement (first, before agent and date)
    # and to a structured place with country "xx" (the source has no country)
    data = {
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "startDate": "2019-12-07",
            "bf:place": {"@type": "bf:Place", "rdfs:label": "Sierre"},
            "bf:agent": {"@type": "bf:Agent", "rdfs:label": "Canal 9 / Kanal 9"},
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["place"] == [{"country": "xx"}]
    assert prov["statement"] == [
        {"label": [{"value": "Sierre"}], "type": "bf:Place"},
        {"label": [{"value": "Canal 9 / Kanal 9"}], "type": "bf:Agent"},
        {"label": [{"value": "2019"}], "type": "Date"},
    ]

    # a missing @type defaults to bf:Publication, and no place field is added
    # when the source has no bf:place
    data = {"bf:provisionActivity": {"startDate": "2000"}}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_provision_activity()
    prov = transformation.json["provisionActivity"][0]
    assert prov["type"] == "bf:Publication"
    assert "place" not in prov


def test_trans_electronic_locator(app):
    """Test transformation electronicLocator."""
    data = {
        "bf:electronicLocator": [
            {
                "@type": "bf:electronicLocator",
                "@id": "https://archives.memovs.ch/thumbnail/urn:avn:75864",
                "bf:noteType": "thumbnail",
            },
            {
                "@type": "bf:electronicLocator",
                "@id": "https://archives.memovs.ch/detail/urn:avn:75864",
                "bf:noteType": "landingPage",
                "rdfs:label": "Fiche détaillée",
            },
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_electronic_locator()
    assert transformation.json == {
        "electronicLocator": [
            {
                "content": "coverImage",
                "type": "relatedResource",
                "url": "https://archives.memovs.ch/thumbnail/urn:avn:75864",
            },
            {
                "content": "webSite",
                "type": "relatedResource",
                "url": "https://archives.memovs.ch/detail/urn:avn:75864",
                "publicNote": ["Fiche détaillée"],
            },
        ],
    }

    # landingPage content reflects the RDA content type (moving image -> film)
    data = {
        "bf:content": {"@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1023"},
        "bf:electronicLocator": [
            {
                "@type": "bf:electronicLocator",
                "@id": "https://archives.memovs.ch/detail/urn:avn:75864",
                "bf:noteType": "landingPage",
            }
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_electronic_locator()
    assert transformation.json["electronicLocator"][0]["content"] == "film"

    # still image -> photography, audio (any subtype) -> audio
    for content_id, expected in (
        ("http://rdaregistry.info/termList/RDAContentType/rdaco:1014", "photography"),
        ("http://rdaregistry.info/termList/RDAContentType/rdaco:1011", "audio"),
    ):
        data = {
            "bf:content": {"@id": content_id},
            "bf:electronicLocator": [
                {
                    "@type": "bf:electronicLocator",
                    "@id": "https://archives.memovs.ch/detail/urn:avn:75864",
                    "bf:noteType": "landingPage",
                }
            ],
        }
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_electronic_locator()
        assert transformation.json["electronicLocator"][0]["content"] == expected


def test_trans_language(app):
    """Test transformation language."""
    # Test with French
    data = {
        "bf:language": [
            {
                "@type": "bf:Language",
                "@id": "http://id.loc.gov/vocabulary/languages/fre",
                "rdfs:label": "fre",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_language()
    assert transformation.json == {"language": [{"type": "bf:Language", "value": "fre"}]}

    # Test with German (ISO 639-2/B code 'deu' should map to MARC 'ger')
    data = {
        "bf:language": [
            {
                "@type": "bf:Language",
                "@id": "http://id.loc.gov/vocabulary/languages/deu",
                "rdfs:label": "deu",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_language()
    assert transformation.json == {"language": [{"type": "bf:Language", "value": "ger"}]}

    # Test with no language (should default to 'zxx' — no linguistic content)
    data = {}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_language()
    assert transformation.json == {"language": [{"type": "bf:Language", "value": "zxx"}]}

    # Test with an empty bf:language list (no linguistic content)
    data = {"bf:language": []}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_language()
    assert transformation.json == {"language": [{"type": "bf:Language", "value": "zxx"}]}


def test_trans_series_statement(app):
    """Test transformation seriesStatement from bf:partOf and bf:seriesStatement."""
    # bf:partOf with noteType prefix
    data = {"bf:partOf": [{"bf:noteType": "Collection", "rdfs:label": "Archives audiovisuelles"}]}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert transformation.json["seriesStatement"] == [
        {"seriesTitle": [{"value": "Collection: Archives audiovisuelles"}]}
    ]

    # bf:partOf label only (no noteType)
    data = {"bf:partOf": [{"rdfs:label": "Archives audiovisuelles"}]}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert transformation.json["seriesStatement"] == [{"seriesTitle": [{"value": "Archives audiovisuelles"}]}]

    # Multiple bf:partOf entries
    data = {
        "bf:partOf": [
            {"bf:noteType": "Collection", "rdfs:label": "Archives audiovisuelles"},
            {"bf:noteType": "Série", "rdfs:label": "Fonds régional"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert transformation.json["seriesStatement"] == [
        {"seriesTitle": [{"value": "Collection: Archives audiovisuelles"}]},
        {"seriesTitle": [{"value": "Série: Fonds régional"}]},
    ]

    # bf:partOf with noteType "fonds" or "emission" is not imported (not necessary)
    data = {
        "bf:partOf": [
            {"bf:noteType": "fonds", "rdfs:label": "Fonds Binder"},
            {"bf:noteType": "Emission", "rdfs:label": "Le Regard valaisan"},
            {"bf:noteType": "Collection", "rdfs:label": "Archives audiovisuelles"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert transformation.json["seriesStatement"] == [
        {"seriesTitle": [{"value": "Collection: Archives audiovisuelles"}]}
    ]

    # bf:seriesStatement is always a list of strings
    data = {"bf:seriesStatement": ["Collection Valaisanne ; 5"]}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert transformation.json["seriesStatement"] == [{"seriesTitle": [{"value": "Collection Valaisanne ; 5"}]}]

    # Both bf:partOf and bf:seriesStatement combined
    data = {
        "bf:partOf": [{"rdfs:label": "Archives audiovisuelles"}],
        "bf:seriesStatement": ["Collection Valaisanne ; 5"],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert transformation.json["seriesStatement"] == [
        {"seriesTitle": [{"value": "Archives audiovisuelles"}]},
        {"seriesTitle": [{"value": "Collection Valaisanne ; 5"}]},
    ]

    # No data
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)
    transformation.trans_series_statement()
    assert "seriesStatement" not in (transformation.json or {})


def test_trans_subjects(app):
    """Test transformation subjects with type validation."""
    # Subjects with an idref @id go to subjects as MEF $ref links when the entity is found
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [
            {"@type": "bf:Topic", "@id": "http://www.idref.fr/027390548", "rdfs:label": "Valais"},
            {"@type": "bf:Person", "@id": "https://www.idref.fr/123456789", "rdfs:label": "Einstein, Albert"},
            {"@type": "bf:Place", "@id": "http://www.idref.fr/987654321", "rdfs:label": "Sion"},
        ],
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_subjects()
    assert len(transformation.json["subjects"]) == 3
    assert transformation.json["subjects"][0] == {
        "entity": {"$ref": "https://mef.rero.ch/api/concepts/idref/027390548"}
    }
    assert transformation.json["subjects"][1] == {"entity": {"$ref": "https://mef.rero.ch/api/agents/idref/123456789"}}
    assert transformation.json["subjects"][2] == {"entity": {"$ref": "https://mef.rero.ch/api/places/idref/987654321"}}
    assert transformation._iconographic_labels == []

    # Subjects without idref @id go to _iconographic_labels (not subjects)
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [
            {"@type": "bf:Topic", "rdfs:label": "homme"},
            {"@type": "bf:Place", "rdfs:label": "Valais"},
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_subjects()
    assert transformation.json is None
    assert transformation._iconographic_labels == ["homme", "Valais"]

    # Mixed: some with idref go to subjects, others without go to _iconographic_labels
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [
            {"@type": "bf:Topic", "@id": "http://www.idref.fr/027390548", "rdfs:label": "Valais (Suisse)"},
            {"@type": "bf:Topic", "rdfs:label": "fête"},
            {"@type": "bf:Temporal", "rdfs:label": "20e siècle"},
        ],
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_subjects()
    assert len(transformation.json["subjects"]) == 1
    assert transformation.json["subjects"][0] == {
        "entity": {"$ref": "https://mef.rero.ch/api/concepts/idref/027390548"}
    }
    assert transformation._iconographic_labels == ["fête", "20e siècle"]

    # Idref not in MEF: fall back to local entity with authorized_access_point and identifiedBy
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [
            {"@type": "bf:Topic", "@id": "http://www.idref.fr/040738159", "rdfs:label": "Valais (Suisse)"},
        ],
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_not_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_subjects()
    assert transformation.json["subjects"] == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Valais (Suisse)",
                "identifiedBy": {"type": "IdRef", "value": "040738159"},
            }
        }
    ]

    # Idref not in MEF and no label: subject is skipped entirely
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [{"@type": "bf:Topic", "@id": "http://www.idref.fr/040738159"}],
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_not_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_subjects()
    assert transformation.json is None

    # Test with missing @type - should be skipped and logged
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [
            {"@type": "bf:Topic", "@id": "http://www.idref.fr/027390548", "rdfs:label": "Valais"},
            {"rdfs:label": "Missing Type Subject"},
        ],
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_subjects()
    assert len(transformation.json["subjects"]) == 1
    assert transformation._iconographic_labels == []

    # Test with invalid entity type - should be skipped and logged
    data = {
        "@id": "urn:avn:12345",
        "bf:subject": [
            {"@type": "bf:Topic", "rdfs:label": "Valid Topic"},
            {"@type": "bf:InvalidType", "rdfs:label": "Invalid Type"},
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_subjects()
    assert transformation.json is None
    assert transformation._iconographic_labels == ["Valid Topic"]


def test_trans_summary(app):
    """Test transformation summary."""
    # bf:summary string is stored directly
    transformation = Transformation(
        data={"bf:summary": "Film documentaire sur la vie dans les villages valaisans."},
        logger=None,
        verbose=False,
        transform=False,
    )
    transformation.trans_summary()
    assert transformation.json == {
        "summary": [{"label": [{"value": "Film documentaire sur la vie dans les villages valaisans."}]}]
    }

    # Subjects without idref collected by trans_subjects go to a general note, not summary
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)
    transformation._iconographic_labels = ["homme", "fête", "Valais"]
    transformation.trans_summary()
    assert "summary" not in transformation.json
    assert transformation.json == {"note": [{"noteType": "general", "label": "homme, fête, Valais"}]}

    # bf:summary and iconographic labels both produce their own field, note appended to existing ones
    transformation = Transformation(
        data={"bf:summary": "Description générale."}, logger=None, verbose=False, transform=False
    )
    transformation.json_dict["note"] = [{"noteType": "otherPhysicalDetails", "label": "stéréo"}]
    transformation._iconographic_labels = ["montagne", "hiver"]
    transformation.trans_summary()
    assert transformation.json == {
        "summary": [{"label": [{"value": "Description générale."}]}],
        "note": [
            {"noteType": "otherPhysicalDetails", "label": "stéréo"},
            {"noteType": "general", "label": "montagne, hiver"},
        ],
    }

    # No bf:summary and no iconographic labels: no entry
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)
    transformation.trans_summary()
    assert transformation.json is None


def test_trans_extent(app):
    """Test transformation extent and duration.

    Memovs always exports bf:extent and bf:duration as plain strings.
    """
    # Test with extent only
    data = {"bf:extent": "1 film numérique (15 min) : couleur, français ; MXF"}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_extent()
    assert transformation.json == {"extent": "1 film numérique (15 min) : couleur, français ; MXF"}

    # Test with duration
    data = {"bf:duration": "00:15:25"}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_extent()
    assert transformation.json == {"duration": ["00:15:25"]}

    # Test with both extent and duration
    data = {
        "bf:extent": "1 bobine de film",
        "bf:duration": "15 min",
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_extent()
    assert transformation.json == {
        "extent": "1 bobine de film",
        "duration": ["15 min"],
    }


def test_trans_table_of_contents(app):
    """Test transformation tableOfContents from bf:tableOfContents."""
    # Single dict with rdfs:label (always wrapped in a list by the source)
    data = {"bf:tableOfContents": [{"rdfs:label": "1. Partie I -- 2. Partie II"}]}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_table_of_contents()
    assert transformation.json == {"tableOfContents": ["1. Partie I -- 2. Partie II"]}

    # List of dicts without startTime
    data = {
        "bf:tableOfContents": [
            {"rdfs:label": "1. Partie I"},
            {"rdfs:label": "2. Partie II"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_table_of_contents()
    assert transformation.json == {"tableOfContents": ["1. Partie I", "2. Partie II"]}

    # startTime is not imported: only the label is kept
    data = {
        "bf:tableOfContents": [
            {"rdfs:label": "Première fanfare", "startTime": "00:00:01"},
            {"rdfs:label": "Deuxième fanfare", "startTime": "00:02:31"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_table_of_contents()
    assert transformation.json == {"tableOfContents": ["Première fanfare", "Deuxième fanfare"]}

    # No field
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)
    transformation.trans_table_of_contents()
    assert transformation.json is None


def test_trans_notes(app):
    """Test transformation notes."""
    # bf:soundCharacteristic → noteType "otherPhysicalDetails"
    data = {"bf:soundCharacteristic": {"rdfs:label": "stéréo"}}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_notes()
    assert transformation.json == {
        "note": [{"noteType": "otherPhysicalDetails", "label": "stéréo"}],
    }

    # bf:note with a "general" type becomes a general document note
    data = {"bf:note": [{"bf:noteType": "general", "rdfs:label": "Note de contenu"}]}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_notes()
    assert transformation.json == {"note": [{"noteType": "general", "label": "Note de contenu"}]}

    # bf:note destined for a local field (vsavmat/vsavgeo/vsavfonds) is NOT a document
    # note — it is written to a LocalField record by ApiMemovs.sync_local_field
    data = {"bf:note": [{"bf:noteType": "vsavgeo", "rdfs:label": "$2 vsavgeo $a chvs-0 $d Valais"}]}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_notes()
    assert transformation.json is None

    # both types together: only the general note reaches the document
    data = {
        "bf:note": [
            {"bf:noteType": "general", "rdfs:label": "Note de contenu"},
            {"bf:noteType": "vsavgeo", "rdfs:label": "$2 vsavgeo $a chvs-0 $d Valais"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_notes()
    assert transformation.json == {"note": [{"noteType": "general", "label": "Note de contenu"}]}


def test_normalize_newlines(app):
    """Test that CRLF and CR line endings become line breaks in the ILS fields."""
    assert normalize_newlines("a\r\nb\rc\nd") == "a\nb\nc\nd"
    assert normalize_newlines({"key": ["a\r\nb", 42, None]}) == {"key": ["a\nb", 42, None]}

    # the source exports Windows line endings in its free text fields
    data = {
        "bf:summary": "Première ligne.\r\nSeconde ligne.",
        "bf:note": [{"bf:noteType": "general", "rdfs:label": "Droits réservés\r\nSon mauvais"}],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    result = transformation.do(data)
    assert result["summary"] == [{"label": [{"value": "Première ligne.\nSeconde ligne."}]}]
    assert result["note"] == [{"noteType": "general", "label": "Droits réservés\nSon mauvais"}]


def test_full_transformation(app):
    """Test full transformation of a complete record."""
    data = {
        "@id": "urn:avn:75864",
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1023",
            "rdfs:label": "image animée bidimensionnelle",
        },
        "bf:title": {
            "@type": "bf:Title",
            "bf:mainTitle": "L'hiver au Lötschental",
            "rdfs:label": "L'hiver au Lötschental",
        },
        "bf:contribution": [
            {
                "@type": "bf:Contribution",
                "bf:agent": {
                    "@type": "bf:Person",
                    "rdfs:label": "Binder, Pantaléon",
                },
                "bf:role": {"@id": "http://id.loc.gov/vocabulary/relators/pht"},
            }
        ],
        "bf:language": [
            {
                "@type": "bf:Language",
                "@id": "http://id.loc.gov/vocabulary/languages/fre",
                "rdfs:label": "fre",
            }
        ],
        "bf:provisionActivity": {
            "@type": "bf:Publication",
            "bf:date": {"rdf:value": "1950"},
        },
        "bf:extent": "1 bobine de film",
        "bf:duration": "15 min",
        "bf:subject": [
            {"@type": "bf:Topic", "rdfs:label": "hiver"},
            {"@type": "bf:Topic", "rdfs:label": "montagne"},
        ],
        "bf:electronicLocator": [
            {
                "@type": "bf:electronicLocator",
                "@id": "https://archives.memovs.ch/thumbnail/urn:avn:75864",
                "bf:noteType": "thumbnail",
            },
            {
                "@type": "bf:electronicLocator",
                "@id": "https://archives.memovs.ch/detail/urn:avn:75864",
                "bf:noteType": "landingPage",
            },
        ],
        "bf:note": [
            {"rdfs:label": "$2 vsavgeo $a chvs-0 $d Valais"},
        ],
    }

    transformation = Transformation(data=data, logger=None, verbose=False, transform=True)
    result = transformation.json

    # Check key fields are present
    assert result["pid"] == "(MEMOVS)75864"
    assert result["type"] == [{"main_type": "docmaintype_movie_series", "subtype": "docsubtype_movie"}]
    assert result["title"][0]["mainTitle"][0]["value"] == "L'hiver au Lötschental"
    assert result["contribution"][0]["entity"]["authorized_access_point"] == "Binder, Pantaléon"
    assert result["contribution"][0]["role"] == ["pht"]
    assert result["language"][0]["value"] == "fre"
    assert result["provisionActivity"][0]["startDate"] == 1950
    assert result["extent"] == "1 bobine de film"
    assert result["duration"] == ["15 min"]
    # subjects without idref go to a general note, searchable but hidden from the main detail view
    assert "subjects" not in result
    assert {"noteType": "general", "label": "hiver, montagne"} in result["note"]
    # thumbnail and landingPage both go to electronicLocator; landingPage content
    # reflects the RDA content type (rdaco:1023, moving image -> film)
    assert result["electronicLocator"][0]["content"] == "coverImage"
    assert result["electronicLocator"][1]["content"] == "film"
    assert result["electronicLocator"][1]["url"] == "https://archives.memovs.ch/detail/urn:avn:75864"
    assert "link" not in result
    # bf:note is handled by ApiMemovs.sync_local_field, not stored in the document
    assert "descriptionModifier" not in result["adminMetadata"]
    assert result["harvested"] is True


def test_language_iso_b_to_marc_mapping(app):
    """Test ISO 639-2/B to MARC language code mappings."""
    test_cases = [
        ("deu", "ger"),  # German
        ("fra", "fre"),  # French
        ("nld", "dut"),  # Dutch
        ("zho", "chi"),  # Chinese
        ("ces", "cze"),  # Czech
        ("ell", "gre"),  # Greek
        ("cym", "wel"),  # Welsh
    ]

    for iso_b_code, expected_marc_code in test_cases:
        data = {
            "bf:language": [
                {
                    "@type": "bf:Language",
                    "rdfs:label": iso_b_code,
                }
            ]
        }
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_language()
        assert transformation.json["language"][0]["value"] == expected_marc_code, (
            f"Failed to map {iso_b_code} to {expected_marc_code}"
        )


def test_trans_usage_and_access_policy(app):
    """Test transformation usageAndAccessPolicy from bf:usageAndAccessPolicy."""
    # bf:rightsStatement is not imported (not necessary)
    data = {
        "bf:rightsStatement": {
            "@id": "https://rightsstatements.org/vocab/InC/1.0/",
            "rdfs:label": "Philippe Schmid, Médiathèque Valais - Martigny",
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_usage_and_access_policy()
    assert transformation.json is None

    # bf:usageAndAccessPolicy as a single dict (the shape Memovs actually sends)
    data = {
        "bf:usageAndAccessPolicy": {"@type": "bf:UsageAndAccessPolicy", "rdfs:label": "open access"},
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_usage_and_access_policy()
    assert transformation.json == {
        "usageAndAccessPolicy": [{"type": "bf:UsageAndAccessPolicy", "label": "open access"}]
    }

    # bf:usageAndAccessPolicy as list (restricted-access documents)
    data = {
        "bf:usageAndAccessPolicy": [
            {"@type": "bf:UsageAndAccessPolicy", "rdfs:label": "open access"},
            {"@type": "bf:UsageAndAccessPolicy", "rdfs:label": "creative commons"},
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_usage_and_access_policy()
    assert transformation.json == {
        "usageAndAccessPolicy": [
            {"type": "bf:UsageAndAccessPolicy", "label": "open access"},
            {"type": "bf:UsageAndAccessPolicy", "label": "creative commons"},
        ]
    }

    # Restricted-access documents carry a second entry, both are imported
    data = {
        "bf:usageAndAccessPolicy": [
            {"@type": "bf:UsageAndAccessPolicy", "rdfs:label": "Droits d'utilisation réservés"},
            {
                "@type": "bf:UsageAndAccessPolicy",
                "rdfs:label": "Document consultable uniquement depuis la Médiathèque Valais",
            },
        ],
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_usage_and_access_policy()
    assert transformation.json == {
        "usageAndAccessPolicy": [
            {"type": "bf:UsageAndAccessPolicy", "label": "Droits d'utilisation réservés"},
            {
                "type": "bf:UsageAndAccessPolicy",
                "label": "Document consultable uniquement depuis la Médiathèque Valais",
            },
        ]
    }

    # No fields
    data = {}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_usage_and_access_policy()
    assert transformation.json is None


def test_trans_color_content(app):
    """Test transformation colorContent from bf:colorContent."""
    # Test with color (rdacc:1003)
    data = {
        "bf:colorContent": [
            {
                "@id": "http://rdaregistry.info/termList/RDAColourContent/rdacc:1003",
                "rdfs:label": "couleur",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_color_content()
    assert transformation.json == {"colorContent": ["rdacc:1003"]}

    # Test with black and white (rdacc:1002)
    data = {
        "bf:colorContent": [
            {
                "@id": "http://rdaregistry.info/termList/RDAColourContent/rdacc:1002",
                "rdfs:label": "noir et blanc",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_color_content()
    assert transformation.json == {"colorContent": ["rdacc:1002"]}

    # Test with multiple colors (list format)
    data = {
        "bf:colorContent": [
            {"@id": "http://rdaregistry.info/termList/RDAColourContent/rdacc:1002"},
            {"@id": "http://rdaregistry.info/termList/RDAColourContent/rdacc:1003"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_color_content()
    assert transformation.json == {"colorContent": ["rdacc:1002", "rdacc:1003"]}

    # Test with no color content
    data = {}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_color_content()
    assert transformation.json is None

    # Test with invalid color code (should be ignored)
    data = {
        "bf:colorContent": [
            {
                "@id": "http://rdaregistry.info/termList/RDAColourContent/rdacc:9999",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_color_content()
    assert transformation.json is None


def test_trans_production_method(app):
    """Test transformation productionMethod from bf:productionMethod."""
    # Test with single production method
    data = {
        "bf:productionMethod": [
            {
                "@id": "http://rdaregistry.info/termList/RDAproductionMethod/rdapm:1001",
                "rdfs:label": "blueline process",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_production_method()
    assert transformation.json == {"productionMethod": ["rdapm:1001"]}

    # Test with multiple production methods (list format)
    data = {
        "bf:productionMethod": [
            {"@id": "http://rdaregistry.info/termList/RDAproductionMethod/rdapm:1007"},
            {"@id": "http://rdaregistry.info/termList/RDAproductionMethod/rdapm:1010"},
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_production_method()
    assert transformation.json == {"productionMethod": ["rdapm:1007", "rdapm:1010"]}

    # Test with no production method
    data = {}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_production_method()
    assert transformation.json is None

    # Test with invalid production method code (should be ignored)
    data = {
        "bf:productionMethod": [
            {
                "@id": "http://rdaregistry.info/termList/RDAproductionMethod/rdapm:9999",
            }
        ]
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_production_method()
    assert transformation.json is None


def test_trans_content_media_carrier(app):
    """Test transformation contentMediaCarrier from bf:content, bf:media, bf:carrier."""
    # Test with content type only
    data = {
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1020",
            "rdfs:label": "two-dimensional moving image",
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    assert transformation.json == {"contentMediaCarrier": [{"contentType": ["rdaco:1020"]}]}

    # Test with content, media, and carrier types
    data = {
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1020",
        },
        "bf:media": {
            "@id": "http://rdaregistry.info/termList/RDAMediaType/rdamt:1008",
        },
        "bf:carrier": {
            "@id": "http://rdaregistry.info/termList/RDACarrierType/rdact:1052",
        },
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    assert transformation.json == {
        "contentMediaCarrier": [
            {
                "contentType": ["rdaco:1020"],
                "mediaType": "rdamt:1008",
                "carrierType": "rdact:1052",
            }
        ]
    }

    # Test with no content (should not create contentMediaCarrier)
    data = {
        "bf:media": {
            "@id": "http://rdaregistry.info/termList/RDAMediaType/rdamt:1008",
        }
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    assert transformation.json is None

    # Test with invalid content type (should be ignored and logged)
    data = {
        "@id": "urn:avn:12345",
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:9999",
        },
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    assert transformation.json is None

    # Test with invalid media type (should be ignored and logged)
    data = {
        "@id": "urn:avn:12345",
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1020",
        },
        "bf:media": {
            "@id": "http://rdaregistry.info/termList/RDAMediaType/rdamt:9999",
        },
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    # Should still have content type but no media type
    assert transformation.json == {"contentMediaCarrier": [{"contentType": ["rdaco:1020"]}]}

    # Test with invalid carrier type for the media type (should be ignored and logged)
    data = {
        "@id": "urn:avn:12345",
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1020",
        },
        "bf:media": {
            "@id": "http://rdaregistry.info/termList/RDAMediaType/rdamt:1008",
        },
        "bf:carrier": {
            "@id": "http://rdaregistry.info/termList/RDACarrierType/rdact:9999",
        },
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    # Should have content and media but no carrier
    assert transformation.json == {
        "contentMediaCarrier": [
            {
                "contentType": ["rdaco:1020"],
                "mediaType": "rdamt:1008",
            }
        ]
    }

    # Test with carrier type but no media type (should be ignored and logged)
    data = {
        "@id": "urn:avn:12345",
        "bf:content": {
            "@id": "http://rdaregistry.info/termList/RDAContentType/rdaco:1020",
        },
        "bf:carrier": {
            "@id": "http://rdaregistry.info/termList/RDACarrierType/rdact:1052",
        },
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_content_media_carrier()
    # Should only have content type (carrier ignored without media)
    assert transformation.json == {"contentMediaCarrier": [{"contentType": ["rdaco:1020"]}]}


def test_trans_genre_form(app):
    """Test transformation genreForm with type validation."""
    # Genre forms with idref @id go to genreForm as MEF $ref links when found in MEF
    data = {
        "bf:genreForm": {
            "@type": "bf:Topic",
            "@id": "http://www.idref.fr/027390548",
            "rdfs:label": "Documentaires",
        }
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_genre_form()
    assert transformation.json == {
        "genreForm": [{"entity": {"$ref": "https://mef.rero.ch/api/concepts/idref/027390548"}}]
    }

    # Idref not in MEF: fall back to local entity with authorized_access_point and identifiedBy
    data = {
        "bf:genreForm": {"@type": "bf:Topic", "@id": "http://www.idref.fr/040738159", "rdfs:label": "Photographies"},
    }
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_not_found(mock_session)
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_genre_form()
    assert transformation.json["genreForm"] == [
        {
            "entity": {
                "type": "bf:Topic",
                "authorized_access_point": "Photographies",
                "identifiedBy": {"type": "IdRef", "value": "040738159"},
            }
        }
    ]

    # Genre form without idref is ignored
    data = {"bf:genreForm": {"@type": "bf:Topic", "rdfs:label": "Films documentaires"}}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_genre_form()
    assert transformation.json is None

    # Invalid type (bf:Person) - should be skipped and logged
    data = {
        "@id": "urn:avn:12345",
        "bf:genreForm": {"@type": "bf:Person", "@id": "http://www.idref.fr/123456789", "rdfs:label": "Invalid Person"},
    }
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_genre_form()
    assert transformation.json is None

    # Test with no genre form
    data = {}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_genre_form()
    assert transformation.json is None


def test_trans_provision_activity_dateless(app):
    """Test the unknown date stub of provision_activity.

    A resource without a date in bf:provisionActivity gets the unknown date
    stub: no @type means the default type, no date statement is fabricated.
    The dcterms dates are deliberately ignored — they tell when the Memovs
    record was created, not when the resource was produced.
    """
    for data in (
        {},
        {"bf:provisionActivity": {}},
        {"dcterms:created": "1975-03-21"},
        {"dcterms:modified": "2003-07-10T00:00:00"},
    ):
        transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
        transformation.trans_provision_activity()
        assert transformation.json["provisionActivity"] == [
            {
                "type": "bf:Publication",
                "startDate": 9999,
                "note": "Date(s) uncertain or unknown",
            }
        ]


def test_trans_extent_edge_cases(app):
    """Test extent with dcterms:extent fallback."""
    # dcterms:extent used when bf:extent is absent
    data = {"dcterms:extent": "2 disques"}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_extent()
    assert transformation.json == {"extent": "2 disques"}

    # bf:extent as plain string
    data = {"bf:extent": "3 bobines"}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_extent()
    assert transformation.json == {"extent": "3 bobines"}

    # duration as a plain string
    data = {"bf:duration": "30 min"}
    transformation = Transformation(data=data, logger=None, verbose=False, transform=False)
    transformation.trans_extent()
    assert transformation.json == {"duration": ["30 min"]}


def test_memovs_id_property(app):
    """Test memovs_id extracts the numeric part correctly."""
    # Normal URN with colons
    t = Transformation(data={"@id": "urn:avn:75864"}, logger=None, verbose=False, transform=False)
    assert t.memovs_id == "75864"

    # No colon in @id — returned as-is
    t = Transformation(data={"@id": "75864"}, logger=None, verbose=False, transform=False)
    assert t.memovs_id == "75864"

    # Missing @id key
    t = Transformation(data={}, logger=None, verbose=False, transform=False)
    assert t.memovs_id == ""


def test_trans_title_missing(app):
    """Test trans_title produces an empty title entry when bf:title is absent."""
    transformation = Transformation(data={}, logger=None, verbose=False, transform=False)
    transformation.trans_title()
    assert transformation.json["title"] == [{"type": "bf:Title"}]


def test_resolve_entity_identifiedby_fallback(app):
    """Test _resolve_entity adds identifiedBy when idref is known but absent from MEF."""
    t = Transformation(data={}, logger=None, verbose=False, transform=False)

    # IdRef known but MEF lookup fails → local entity with identifiedBy
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_not_found(mock_session)
        result = t._resolve_entity("http://www.idref.fr/040738159", "bf:Topic", "Valais")
    assert result == {
        "authorized_access_point": "Valais",
        "type": "bf:Topic",
        "identifiedBy": {"type": "IdRef", "value": "040738159"},
    }

    # IdRef known but MEF lookup fails and no label → None (skip)
    with patch(_REQUESTS_SESSION_PATCH) as mock_session:
        _mock_mef_not_found(mock_session)
        result = t._resolve_entity("http://www.idref.fr/040738159", "bf:Topic", "")
    assert result is None

    # No idref URI, label only → local entity without identifiedBy
    result = t._resolve_entity("", "bf:Place", "Sion")
    assert result == {"authorized_access_point": "Sion", "type": "bf:Place"}
    assert "identifiedBy" not in result
