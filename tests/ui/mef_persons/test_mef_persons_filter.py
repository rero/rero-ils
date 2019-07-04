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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Jinja2 filters tests."""

from rero_ils.modules.mef_persons.views import person_label, \
    person_merge_data_values


def test_person_label(app, mef_person_data):
    """Test persons merge data."""
    app.config['RERO_ILS_PERSONS_LABEL_ORDER'] = {
        'fallback': 'fr',
        'fr': ['rero', 'bnf', 'gnd'],
        'de': ['gnd', 'rero', 'bnf'],
    }
    label = person_label(mef_person_data, 'fr')
    assert label == 'Arnoudt, Pierre J.'
    label = person_label(mef_person_data, 'it')
    assert label == 'Arnoudt, Pierre J.'


def test_person_merge_data_values(app, mef_person_data):
    """Test persons merge data."""
    app.config['RERO_ILS_PERSONS_SOURCES'] = ['bnf', 'gnd', 'rero']
    data = person_merge_data_values(mef_person_data)
    assert data == {
        "$schema": {
            "https://mef.test.rero.ch/schemas/authorities/"
            "bnf-person-v0.0.1.json": [
                "bnf"
            ],
            "https://mef.test.rero.ch/schemas/authorities/"
            "gnd-person-v0.0.1.json": [
                "gnd"
            ],
            "https://mef.test.rero.ch/schemas/authorities/"
            "rero-person-v0.0.1.json": [
                "rero"
            ]
        },
        "authorized_access_point_representing_a_person": {
            "Aernoudt, Pierre, 1811-1865": [
                "bnf"
            ],
            "Arnoudt, Pierre J., 1811-1865": [
                "gnd",
                "rero"
            ]
        },
        "biographical_information": {
            "Écrivit aussi en latin": [
                "bnf"
            ],
            "Jésuite (à partir de 1835 ; ordonné prêtre en 1843)": [
                "bnf"
            ],
            "Vécut aux États-Unis à partir de 1835": [
                "bnf"
            ],
            "Vollständiger Vorname: Peter Joseph": [
                "gnd"
            ],
            "Jésuite (à partir de 1835 ; ordonné prêtre en 1843) ; "
            "vécut aux Etats-Unis à partir de 1835, écrivit aussi en latin": [
                "rero"
            ]
        },
        "date_of_birth": {
            "1811-05-17": [
                "bnf"
            ],
            "11.05.1811": [
                "gnd"
            ],
            "1811": [
                "rero"
            ]
        },
        "date_of_death": {
            "1865-07-29": [
                "bnf"
            ],
            "29.07.1865": [
                "gnd"
            ],
            "1865": [
                "rero"
            ]
        },
        "gender": {
            "male": [
                "bnf"
            ]
        },
        "identifier_for_person": {
            "http://catalogue.bnf.fr/ark:/12148/cb10001899h": [
                "bnf"
            ],
            "http://d-nb.info/gnd/172759757": [
                "gnd"
            ],
            "http://data.rero.ch/02-A017671081": [
                "rero"
            ]
        },
        "language_of_person": {
            "fre": [
                "bnf"
            ]
        },
        "md5": {
            "ecc9695462cd840462e3d0af39386fa3": [
                "bnf"
            ],
            "81734e9587b85ef91f895999de92861e": [
                "gnd"
            ],
            "a33cbda21ed35959bcac921de5523b5c": [
                "rero"
            ]
        },
        "pid": {
            "10001899": [
                "bnf"
            ],
            "172759757": [
                "gnd"
            ],
            "A017671081": [
                "rero"
            ]
        },
        "preferred_name_for_person": {
            "Aernoudt, Pierre": [
                "bnf"
            ],
            "Arnoudt, Pierre J.": [
                "gnd",
                "rero"
            ]
        },
        "variant_name_for_person": {
            "Arnoudt, Pierre": [
                "bnf",
                "gnd"
            ],
            "Aernoudt, Pierre-Jacques-Marie": [
                "bnf"
            ],
            "Arnold, Pierre": [
                "bnf",
                "gnd"
            ],
            "Arnoldus, Petrus": [
                "bnf"
            ],
            "Arnoldo, Pierre": [
                "bnf"
            ],
            "Arnold, J.": [
                "bnf",
                "gnd"
            ],
            "Arnoudt, Pierre Joseph": [
                "gnd"
            ],
            "Arnold, Petrus": [
                "gnd"
            ],
            "Arnoudt, P. J.": [
                "gnd"
            ],
            "Arnoudt, P.": [
                "gnd"
            ],
            "Arnold, P. J.": [
                "gnd"
            ],
            "Arnold, Peter J.": [
                "gnd"
            ],
            "Arnold, Peter Joseph": [
                "gnd"
            ],
            "Arnold, Joseph": [
                "gnd",
                "rero"
            ],
            "Arnoudt, Petrus": [
                "gnd"
            ],
            "Aernoudt, Pierre": [
                "gnd",
                "rero"
            ],
            "Arnoudt, Peter J.": [
                "gnd"
            ],
            "Arnoudt, Pierre Jean": [
                "gnd"
            ],
            "Arnold, Josef": [
                "gnd"
            ]
        }
    }
