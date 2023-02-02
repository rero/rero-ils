# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Document utils tests."""

from __future__ import absolute_import, print_function

from rero_ils.modules.documents.extensions import TitleExtension


def test_format_text():
    """Test title format text head."""
    data = [{
        'mainTitle': [{
            'value': 'Dingding lixianji'
        }, {
            'value': '\u4e01\u4e01\u5386\u9669\u8bb0',
            'language': 'und-hani'
        }],
        'type': 'bf:Title'
    }]
    assert '\u4e01\u4e01\u5386\u9669\u8bb0' == TitleExtension.format_text(data)

    data = [{
        'mainTitle': [{
            'value': 'Die russischen orthodoxen Bischöfe von 1893',
        }],
        'subtitle': [{
            'value': 'Bio-Bibliographie'
        }],
        'type': 'bf:Title'
    }]
    assert 'Die russischen orthodoxen Bischöfe von 1893 ' \
           ': Bio-Bibliographie' == TitleExtension.format_text(data)

    data = [{
        'mainTitle': [{
            'value': 'Die russischen orthodoxen Bischöfe von 1893',
        }, {
            'value': 'The Russian Orthodox Bishops of 1893',
            'language': 'eng'
        }],
        'subtitle': [{
            'value': 'Bio-Bibliographie'
        }],
        'type': 'bf:Title'
    }]
    assert 'The Russian Orthodox Bishops of 1893' == \
        TitleExtension.format_text(data)

    data = [{
        'mainTitle': [{
            'value': 'main_title_text',
        }],
        'subtitle': [{
            'value': 'subtitle_text'
        }],
        'part': [
            {
                'partName': [{'value': 'part1'}, {'value': 'part1.1'}],
                'partNumber': [{'value': 'number1'}, {'value': 'number1.1'}],
            },
            {
                'partNumber': [{'value': 'number2'}, {'value': 'number2.2'}],
                'partName': [{'value': 'part2'}]
            }
        ],
        'type': 'bf:Title'
    }]
    assert 'main_title_text : subtitle_text. '\
        'number1, number1.1, part1, part1.1. number2, number2.2, part2' == \
           TitleExtension.format_text(data)

    data = [{
        "mainTitle": [
            {
                "language": "rus-latn",
                "value": "Frant︠s︡uzsko-russkiĭ slovarʹ"
            },
            {
                "language": "rus-cyrl",
                "value": "Французско-русский словарь"
            }
        ],
        "subtitle": [
            {
                "language": "rus-latn",
                "value": "okolo 25 000 slov"
            },
            {
                "language": "rus-cyrl",
                "value": "около 25 000 слов"
            }
        ],
        "type": "bf:Title"
    }]
    assert 'Французско-русский словарь : около 25 000 слов' == \
        TitleExtension.format_text(data)
