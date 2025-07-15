# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Test api harvester cantook dojson."""

import json
from os.path import dirname, join

from rero_ils.modules.api_harvester.cantook.dojson.json import Transformation


def clean_dict(data, keys=("$schema", "adminMetadata", "fiction_statement")):
    """
    Clean keys from dictionary.

    :param keys: keys to clean from dictionary.
    :param data: dictionary to clean.
    """
    for key in keys:
        data.pop(key, None)
    return data


def test_trans_constants(app):
    """Test transformation constants."""

    data = {}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_constants()
    assert transformation.json == {
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json",
        "adminMetadata": {"encodingLevel": "Not applicable"},
        "harvested": True,
        "issuance": {"main_type": "rdami:1001", "subtype": "materialUnit"},
        "type": [{"main_type": "docmaintype_book", "subtype": "docsubtype_e-book"}],
    }


def test_trans_pid(app):
    """Test transformation pid."""
    data = {"id": "immateriel.frO1097420"}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_pid()
    assert transformation.json == {"pid": "cantook-immateriel.frO1097420"}


def test_trans_identified_by(app):
    """Test transformation IdentifiedBy."""
    data = {
        "id": "immateriel.frO1097420",
        "media": [
            {
                "nature": "epub",
                "key_type": "isbn13",
                "id": "immateriel.frO1097420-9782354089597-epub",
                "key": "9782354089597",
                "issued_on": "2024-12-04T06:00:00+01:00",
                "current_holds": 0,
            },
            {
                "nature": "paper",
                "key_type": "isbn13",
                "id": "immateriel.frO1097420-9782354089412-paper",
                "key": "9782354089412",
                "issued_on": "2024-12-04T06:00:00+01:00",
                "current_holds": 0,
            },
        ],
    }
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_identified_by()
    assert transformation.json == {
        "identifiedBy": [
            {
                "source": "CANTOOK",
                "type": "bf:Local",
                "value": "cantook-immateriel.frO1097420",
            },
            {"note": "epub", "type": "bf:Isbn", "value": "9782354089597"},
            {"note": "paper", "type": "bf:Isbn", "value": "9782354089412"},
        ],
    }
    data = {
        "id": "immateriel.frO1097420",
        "media": [
            {
                "nature": "audio",
                "key_type": "isbn13",
                "id": "immateriel.frO1097420-9782354089597-epub",
                "key": "9782354089597",
                "issued_on": "2024-12-04T06:00:00+01:00",
                "current_holds": 0,
            },
        ],
    }
    # test audio type
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_identified_by()
    assert transformation.json == {
        "identifiedBy": [
            {
                "source": "CANTOOK",
                "type": "bf:Local",
                "value": "cantook-immateriel.frO1097420",
            },
            {"note": "audio", "type": "bf:Isbn", "value": "9782354089597"},
        ],
        "type": [
            {"main_type": "docmaintype_audio", "subtype": "docsubtype_audio_book"}
        ],
    }


def test_trans_title(app):
    """Test transformation Title."""
    data = {
        "title": "L'argent des gens",
        "title_prefix": None,
        "title_sort": "l'argent des gens",
        "subtitle": None,
    }
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_title()
    assert transformation.json == {
        "title": [{"mainTitle": [{"value": "L'argent des gens"}], "type": "bf:Title"}]
    }
    # with sub title
    data = {
        "title": "L'argent des gens",
        "title_prefix": None,
        "title_sort": "l'argent des gens",
        "subtitle": "Tentative d'épuisement de notre porte-monnaie",
    }
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_title()
    assert transformation.json == {
        "title": [
            {
                "mainTitle": [{"value": "L'argent des gens"}],
                "subtitle": [
                    {"value": "Tentative d'épuisement de notre porte-monnaie"}
                ],
                "type": "bf:Title",
            }
        ],
    }


def test_trans_contribution(app):
    """Test transformation Contribution."""
    data = {
        "contributors": [
            {
                "first_name": "Jean",
                "last_name": "Guiloineau",
                "nature": "translated_by",
                "country": "FR",
                "biography": "Jean Guiloineau est le traducteur des premiers romans de Toni Morrison L\u2019\u0152il le plus bleu, Le Chant de Salomon, Paradis et Tar Baby, parus chez Christian Bourgois \u00e9diteur. Il traduit \u00e9galement d\u2019autres auteurs embl\u00e9matiques de la litt\u00e9rature anglo-saxonne, entre autres Nelson Mandela, Nadine Gordimer, Salman Rushdie, Angela Carter, Thomas McGuane et Ben Okri.",
                "website": "",
            },
            {
                "first_name": "Toni",
                "last_name": "Morrison",
                "nature": "author",
                "country": "FR",
                "biography": "",
                "website": "",
            },
            # again the same entity
            {
                "first_name": "Toni",
                "last_name": "Morrison",
                "nature": "author",
                "country": "FR",
                "biography": "",
                "website": "",
            },
        ],
    }
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_contribution()
    assert transformation.json == {
        "contribution": [
            {
                "entity": {
                    "authorized_access_point": "Guiloineau, Jean",
                    "type": "bf:Person",
                },
                "role": ["trl"],
            },
            {
                "entity": {
                    "authorized_access_point": "Morrison, Toni",
                    "type": "bf:Person",
                },
                "role": ["aut"],
            },
        ],
    }


def test_trans_provision_activity(app):
    """Transform provisionActivity."""
    data = {
        "publisher_name": "Éditions Mnémos",
        "created_at": "2022-03-09T07:45:09+01:00",
    }
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_provision_activity()
    assert transformation.json == {
        "provisionActivity": [
            {
                "startDate": 2022,
                "statement": [
                    {"label": [{"value": "Éditions Mnémos"}], "type": "bf:Agent"},
                    {"label": [{"value": "2022"}], "type": "Date"},
                ],
                "type": "bf:Publication",
            }
        ],
    }


def test_trans_electronic_locator(app):
    """Test transformation electronicLocator."""
    data = {
        "cover": "https://images.immateriel.fr/covers/4MY6AC5.png",
        "flipbook": "https://tw5.immateriel.fr/wiki/immateriel/b/4MY6AC5",
    }
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_electronic_locator()
    assert transformation.json == {
        "electronicLocator": [
            {
                "content": "coverImage",
                "type": "relatedResource",
                "url": "https://images.immateriel.fr/covers/4MY6AC5.png",
            },
            {
                "content": "extract",
                "type": "relatedResource",
                "url": "https://tw5.immateriel.fr/wiki/immateriel/b/4MY6AC5",
            },
        ],
    }


def test_trans_fiction(app):
    """Test transformation fiction."""
    data = {"fiction": None}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_fiction()
    assert transformation.json == {"fiction_statement": "unspecified"}


def test_trans_language(app):
    """Test transformation language."""
    data = {"languages": ["fre"]}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_language()
    assert transformation.json == {
        "language": [{"type": "bf:Language", "value": "fre"}]
    }


def test_trans_orginal_language(app):
    """Test transformation language."""
    data = {"translated_from": "eng"}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_orginal_language()
    assert transformation.json == {"originalLanguage": ["eng"]}


# def test_trans_subjects(app):
#     """Test transformation Subject."""
#     data = {
#         "classifications": [
#             {
#                 "standard": "bisac",
#                 "identifiers": ["FIC009000"],
#                 "captions": [{"fr": None, "en": None}],
#             },
#             {
#                 "standard": "cantook",
#                 "identifiers": ["science-fiction-fantasy"],
#                 "captions": [
#                     {
#                         "fr": "Romans science-fiction et fantastique",
#                         "en": "Science Fiction & Fantasy",
#                     }
#                 ],
#             },
#             {
#                 "standard": "feedbooks",
#                 "identifiers": ["FBFIC009000"],
#                 "captions": [{"fr": "Fantasy", "en": "Fantasy"}],
#             },
#             {
#                 "standard": "thema",
#                 "identifiers": ["FM"],
#                 "captions": [{"fr": "Fantasy", "en": "Fantasy"}],
#             },
#         ]
#     }
#     transformation = Transformation(
#         data=data, logger=None, verbose=False, transform=False
#     )
#     transformation.trans_subjects()
#     assert transformation.json == {
#         "subjects": [
#             {
#                 "entity": {
#                     "authorized_access_point": "Romans science-fiction "
#                     "et fantastique",
#                     "type": "bf:Topic",
#                 }
#             }
#         ],
#     }


def test_trans_summary(app):
    """Test transformation Summary."""
    data = {"summary": "This is a summery."}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_summary()
    assert transformation.json == {
        "summary": [{"label": [{"value": "This is a summery."}]}]
    }


def test_trans_extent(app):
    """Test transformation Extend."""
    data = {"page_count": 560}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_extent()
    assert transformation.json == {"extent": "560 pages"}


# to be used to create holdings
def test_trans_links(app):
    """Test transformation links."""
    data = {"link": "https://bm.ebibliomedia.ch/resources/648bf704b7e14d000154685f"}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_links()
    assert transformation.json == {
        "link": "https://bm.ebibliomedia.ch/resources/648bf704b7e14d000154685f"
    }


# to be used for deleted records
def test_trans_deleted(app):
    """Test transformation deleted."""
    data = {"unavailable_since": "2024-01-03T16:50:35+01:00"}
    transformation = Transformation(
        data=data, logger=None, verbose=False, transform=False
    )
    transformation.trans_deleted()
    assert transformation.json == {"deleted": "2024-01-03T16:50:35+01:00"}


def test_trans_do(app):
    """Test dojson do."""
    content = json.load(
        open(join(dirname(__file__), "../../data/mv_cantook_deleted.json"))
    )
    data = content["resources"][0]
    transformation = Transformation(logger=None, verbose=False, transform=False)
    result = transformation.do(data)
    assert result == {
        "$schema": "https://bib.rero.ch/schemas/documents/document-v0.0.1.json",
        "adminMetadata": {"encodingLevel": "Not applicable"},
        "contribution": [
            {
                "entity": {
                    "authorized_access_point": "Party, Adrien",
                    "type": "bf:Person",
                },
                "role": ["aut"],
            }
        ],
        "deleted": "2002-02-02",
        "electronicLocator": [
            {
                "content": "coverImage",
                "type": "relatedResource",
                "url": "https://images.immateriel.fr/covers/5V4JHTA.png",
            },
            {
                "content": "extract",
                "type": "relatedResource",
                "url": "https://tw5.immateriel.fr/wiki/immateriel/b/5V4JHTA",
            },
        ],
        "extent": "735 pages",
        "fiction_statement": "unspecified",
        "harvested": True,
        "identifiedBy": [
            {
                "source": "CANTOOK",
                "type": "bf:Local",
                "value": "cantook-immateriel.frO1109367",
            },
            {"note": "epub", "type": "bf:Isbn", "value": "9782376865193"},
            {"note": "paper", "type": "bf:Isbn", "value": "9782376866688"},
        ],
        "issuance": {"main_type": "rdami:1001", "subtype": "materialUnit"},
        "language": [{"type": "bf:Language", "value": "fre"}],
        "link": "https://mediatheque-valais.cantookstation.eu/resources/642bb98ebf82c100014867a4",
        "pid": "cantook-immateriel.frO1109367",
        "provisionActivity": [
            {
                "startDate": 2023,
                "statement": [
                    {
                        "label": [{"value": "Nouvelles Éditions Actu SF"}],
                        "type": "bf:Agent",
                    },
                    {"label": [{"value": "2023"}], "type": "Date"},
                ],
                "type": "bf:Publication",
            }
        ],
        # "subjects": [
        #     {
        #         "entity": {
        #             "authorized_access_point": "Romans science-fiction "
        #             "et fantastique",
        #             "type": "bf:Topic",
        #         }
        #     }
        # ],
        "summary": [
            {
                "label": [
                    {
                        "value": "Les vampires hantent toujours aujourd'hui "
                        "nos cauchemars. Depuis leurs débuts, ils "
                        "ont essaimé dans la littérature, le cinéma, "
                        "le théâtre, les séries, la BD, le jeu de "
                        "rôle, la musique... aucun média n'a échappé "
                        "à la fascination qu'ils exercent sur nous, "
                        "pauvres mortels. Vampirologie est un "
                        "ouvrage clef pour comprendre le phénomène, "
                        "..."
                    }
                ]
            }
        ],
        "title": [{"mainTitle": [{"value": "Vampirologie"}], "type": "bf:Title"}],
        "type": [{"main_type": "docmaintype_book", "subtype": "docsubtype_e-book"}],
    }
