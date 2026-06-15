# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Document utils tests."""

from rero_ils.modules.documents.extensions import TitleExtension


def test_format_text():
    """Test title format text head."""
    data = [
        {
            "mainTitle": [
                {"value": "Dingding lixianji"},
                {"value": "\u4e01\u4e01\u5386\u9669\u8bb0", "language": "und-hani"},
            ],
            "type": "bf:Title",
        }
    ]
    assert TitleExtension.format_text(data) == "\u4e01\u4e01\u5386\u9669\u8bb0"

    data = [
        {
            "mainTitle": [
                {
                    "value": "Die russischen orthodoxen Bischöfe von 1893",
                }
            ],
            "subtitle": [{"value": "Bio-Bibliographie"}],
            "type": "bf:Title",
        }
    ]
    assert TitleExtension.format_text(data) == "Die russischen orthodoxen Bischöfe von 1893 : Bio-Bibliographie"

    data = [
        {
            "mainTitle": [
                {
                    "value": "Die russischen orthodoxen Bischöfe von 1893",
                },
                {"value": "The Russian Orthodox Bishops of 1893", "language": "eng"},
            ],
            "subtitle": [{"value": "Bio-Bibliographie"}],
            "type": "bf:Title",
        }
    ]
    assert TitleExtension.format_text(data) == "The Russian Orthodox Bishops of 1893"

    data = [
        {
            "mainTitle": [
                {
                    "value": "main_title_text",
                }
            ],
            "subtitle": [{"value": "subtitle_text"}],
            "part": [
                {
                    "partName": [{"value": "part1"}, {"value": "part1.1"}],
                    "partNumber": [{"value": "number1"}, {"value": "number1.1"}],
                },
                {
                    "partNumber": [{"value": "number2"}, {"value": "number2.2"}],
                    "partName": [{"value": "part2"}],
                },
            ],
            "type": "bf:Title",
        }
    ]
    assert (
        TitleExtension.format_text(data) == "main_title_text : subtitle_text. "
        "number1, number1.1, part1, part1.1. number2, number2.2, part2"
    )

    data = [
        {
            "mainTitle": [
                {"language": "rus-latn", "value": "Frant︠s︡uzsko-russkiĭ slovarʹ"},
                {"language": "rus-cyrl", "value": "Французско-русский словарь"},
            ],
            "subtitle": [
                {"language": "rus-latn", "value": "okolo 25 000 slov"},
                {"language": "rus-cyrl", "value": "около 25 000 слов"},
            ],
            "type": "bf:Title",
        }
    ]
    assert TitleExtension.format_text(data) == "Французско-русский словарь : около 25 000 слов"
